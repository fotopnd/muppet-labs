from __future__ import annotations

import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from eval.config import DEFAULT_RUBRICS_DIR, resolve_db_path
from eval.db import (
    get_db,
    get_last_two_completed_runs,
    get_results_for_run,
    get_run,
    get_run_by_label,
    init_db,
    insert_result,
    insert_run,
    insert_test_case,
    list_runs,
    update_run,
)
from eval.models import DatasetSource, EvalRun, ModelBackend, Rubric, RunConfig, TestCase

app = typer.Typer(name="eval", help="Model behaviour evaluation harness.", add_completion=False)


def _console(no_color: bool = False) -> Console:
    return Console(no_color=no_color or not sys.stdout.isatty())


@app.command("run")
def cmd_run(
    model: Annotated[str, typer.Option(help="Model name, e.g. qwen2.5:7b or claude-sonnet-4-6")],
    backend: Annotated[
        str | None,
        typer.Option(help="local or claude. Inferred from model name if omitted."),
    ] = None,
    config: Annotated[Path | None, typer.Option(help="YAML RunConfig file.")] = None,
    dataset: Annotated[
        list[str] | None, typer.Option(help="Dataset name(s). Repeatable. Default: custom.")
    ] = None,
    cases: Annotated[Path | None, typer.Option(help="Custom YAML test case file.")] = None,
    rubric: Annotated[
        list[Path] | None, typer.Option(help="Rubric YAML file(s). Repeatable.")
    ] = None,
    label: Annotated[str | None, typer.Option(help="Human-readable run label.")] = None,
    limit: Annotated[int | None, typer.Option(help="Max cases per dataset.")] = None,
    db: Annotated[Path | None, typer.Option(help="SQLite DB path.")] = None,
    judge_model: Annotated[
        str, typer.Option(help="Claude model for LLM-as-judge.")
    ] = "claude-sonnet-4-6",
    no_judge: Annotated[
        bool, typer.Option("--no-judge", help="Skip LLM-as-judge scoring.")
    ] = False,
) -> None:
    from eval.datasets import load_dataset
    from eval.rubrics import get_applicable_rubrics, load_rubric
    from eval.runner import run_case
    from eval.scorer import score_result

    con = _console()
    db_path = resolve_db_path(db)
    init_db(db_path)

    # --- Build RunConfig ---
    if config:
        from eval.config import load_run_config

        run_config = load_run_config(config)
    else:
        resolved_backend = backend or ("claude" if model.startswith("claude-") else "local")
        try:
            mb = ModelBackend(resolved_backend)
        except ValueError:
            con.print(f"[red]Unknown backend '{resolved_backend}'. Use 'local' or 'claude'.[/red]")
            raise typer.Exit(1) from None
        dataset_list = dataset or ["custom"]
        try:
            sources = [DatasetSource(d) for d in dataset_list]
        except ValueError as exc:
            con.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc
        rubric_list = rubric or []
        rubric_names = [r.stem for r in rubric_list]
        run_config = RunConfig(
            model_backend=mb,
            model_name=model,
            dataset_names=sources,
            rubric_names=rubric_names,
            judge_model=judge_model,
            dataset_limit=limit,
            run_label=label,
        )

    # --- Load rubrics ---
    rubric_paths = list(rubric or [])
    # For any rubric name not supplied as a path, search DEFAULT_RUBRICS_DIR
    supplied_names = {p.stem for p in rubric_paths}
    for rname in run_config.rubric_names:
        if rname not in supplied_names:
            candidate = DEFAULT_RUBRICS_DIR / f"{rname}.yaml"
            if candidate.exists():
                rubric_paths.append(candidate)
    all_rubrics: dict[str, Rubric] = {}
    for rpath in rubric_paths:
        rb = load_rubric(rpath)
        all_rubrics[rb.name] = rb

    # --- Load datasets ---
    all_cases: list[TestCase] = []
    for source in run_config.dataset_names:
        all_cases.extend(load_dataset(source, run_config, cases_path=cases))

    if not all_cases:
        con.print("[yellow]No test cases loaded. Use --cases or --dataset.[/yellow]")
        raise typer.Exit(0)

    # --- Create run record ---
    run = EvalRun(config=run_config, total_cases=len(all_cases))
    with get_db(db_path) as conn:
        insert_run(conn, run)

    con.print(
        f"[bold]Run:[/bold] {run.id[:8]}  model={run_config.model_name}  cases={len(all_cases)}"
    )

    # --- Execute cases ---
    results = []
    errors = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=con,
    ) as progress:
        task = progress.add_task("Evaluating...", total=len(all_cases))
        for case in all_cases:
            applicable = get_applicable_rubrics(case, all_rubrics)
            try:
                response = run_case(case, run_config)
                result = score_result(
                    case,
                    response,
                    applicable,
                    judge_model,
                    run_id=run.id,
                    skip_judge=no_judge,
                )
            except Exception as exc:
                con.print(f"[red]Error on case {case.id}: {exc}[/red]")
                errors += 1
                progress.advance(task)
                continue
            results.append(result)
            with get_db(db_path) as conn:
                insert_result(conn, result)
            progress.advance(task)

    # --- Compute summary stats ---
    scored = [r.aggregate_score for r in results if r.aggregate_score is not None]
    run.mean_score = sum(scored) / len(scored) if scored else None

    total = len(results)
    if total:
        correct_refusals = sum(1 for r in results if r.refusal_detected == r.expect_refusal)
        run.refusal_rate = correct_refusals / total
    else:
        run.refusal_rate = None

    run.finished_at = datetime.now(UTC)
    run.status = "failed" if errors and not results else "complete"
    run.total_cases = len(all_cases)

    with get_db(db_path) as conn:
        update_run(conn, run)

    # --- Summary table ---
    t = Table(title="Run Summary", show_header=True, header_style="bold")
    t.add_column("Field")
    t.add_column("Value")
    t.add_row("Run ID", run.id[:8])
    t.add_row("Model", run_config.model_name)
    t.add_row("Cases run", str(len(results)))
    t.add_row("Errors", str(errors))
    t.add_row("Mean score", f"{run.mean_score:.3f}" if run.mean_score is not None else "—")
    refusal_str = f"{run.refusal_rate:.3f}" if run.refusal_rate is not None else "—"
    t.add_row("Refusal accuracy", refusal_str)
    t.add_row("Status", run.status)
    con.print(t)


@app.command("add-case")
def cmd_add_case(
    prompt: Annotated[str | None, typer.Option(help="Prompt text.")] = None,
    file: Annotated[Path | None, typer.Option(help="YAML file of test cases to import.")] = None,
    id: Annotated[
        str | None, typer.Option(help="Stable case ID. Auto-generated if omitted.")
    ] = None,
    tag: Annotated[list[str] | None, typer.Option(help="Tag(s). Repeatable.")] = None,
    rubric: Annotated[list[str] | None, typer.Option(help="Rubric name(s). Repeatable.")] = None,
    expect_refusal: Annotated[bool, typer.Option("--expect-refusal")] = False,
    reference: Annotated[str | None, typer.Option(help="Reference/correct answer.")] = None,
    db: Annotated[Path | None, typer.Option(help="SQLite DB path.")] = None,
) -> None:
    import sqlite3

    from eval.datasets.custom import load_custom_cases

    con = _console()
    db_path = resolve_db_path(db)
    init_db(db_path)

    cases: list[TestCase] = []
    if file:
        cases = load_custom_cases(file)
    elif prompt:
        auto_id = id or "custom:" + hashlib.sha1(prompt.encode()).hexdigest()[:8]
        cases = [
            TestCase(
                id=auto_id,
                prompt=prompt,
                dataset=DatasetSource.CUSTOM,
                tags=list(tag or []),
                expect_refusal=expect_refusal,
                reference_answer=reference,
                rubric_names=list(rubric or []),
            )
        ]
    else:
        con.print("[red]Provide --prompt TEXT or --file PATH.[/red]")
        raise typer.Exit(1)

    inserted = 0
    skipped = 0
    with get_db(db_path) as conn:
        for case in cases:
            try:
                insert_test_case(conn, case)
                inserted += 1
                con.print(f"Added: {case.id}")
            except sqlite3.IntegrityError:
                con.print(f"[yellow]Warning: case '{case.id}' already exists, skipping.[/yellow]")
                skipped += 1

    con.print(f"\n{inserted} case(s) added, {skipped} skipped.")
    if inserted == 0 and skipped > 0:
        raise typer.Exit(1)


@app.command("diff")
def cmd_diff(
    run_a: Annotated[str | None, typer.Argument(help="Baseline run ID or label.")] = None,
    run_b: Annotated[str | None, typer.Argument(help="Current run ID or label.")] = None,
    db: Annotated[Path | None, typer.Option(help="SQLite DB path.")] = None,
    no_color: Annotated[bool, typer.Option("--no-color")] = False,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    from eval.drift import compute_drift, format_drift_report

    con = _console(no_color)
    db_path = resolve_db_path(db)
    init_db(db_path)

    with get_db(db_path) as conn:
        if run_a and run_b:
            era = _resolve_run(conn, run_a)
            erb = _resolve_run(conn, run_b)
        else:
            pair = get_last_two_completed_runs(conn)
            if pair is None:
                con.print("[red]Need at least two completed runs to compute drift.[/red]")
                raise typer.Exit(1)
            era, erb = pair
        if era is None or erb is None:
            con.print("[red]One or both runs not found.[/red]")
            raise typer.Exit(1)
        results_a = get_results_for_run(conn, era.id)
        results_b = get_results_for_run(conn, erb.id)

    report = compute_drift(era, results_a, erb, results_b)

    if json_out:
        print(report.model_dump_json(indent=2))
    else:
        print(format_drift_report(report, use_color=not no_color))


@app.command("list")
def cmd_list(
    limit: Annotated[int, typer.Option(help="Number of runs to show.")] = 10,
    status: Annotated[str, typer.Option(help="running|complete|failed|all")] = "all",
    db: Annotated[Path | None, typer.Option(help="SQLite DB path.")] = None,
) -> None:
    con = _console()
    db_path = resolve_db_path(db)
    init_db(db_path)

    with get_db(db_path) as conn:
        runs = list_runs(conn, limit=limit, status=None if status == "all" else status)

    if not runs:
        con.print("No runs found.")
        return

    t = Table(title="Eval Runs", show_header=True, header_style="bold")
    t.add_column("ID", style="cyan")
    t.add_column("Label")
    t.add_column("Backend")
    t.add_column("Model")
    t.add_column("Datasets")
    t.add_column("Cases", justify="right")
    t.add_column("Score", justify="right")
    t.add_column("Refusal", justify="right")
    t.add_column("Status")
    t.add_column("Started")

    for run in runs:
        c = run.config
        t.add_row(
            run.id[:8],
            c.run_label or "—",
            c.model_backend.value,
            c.model_name,
            ",".join(d.value for d in c.dataset_names),
            str(run.total_cases),
            f"{run.mean_score:.2f}" if run.mean_score is not None else "—",
            f"{run.refusal_rate:.2f}" if run.refusal_rate is not None else "—",
            run.status,
            run.started_at.strftime("%Y-%m-%d %H:%M"),
        )
    con.print(t)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _resolve_run(conn, ref: str):
    """Try run ID then label."""
    r = get_run(conn, ref)
    if r:
        return r
    return get_run_by_label(conn, ref)
