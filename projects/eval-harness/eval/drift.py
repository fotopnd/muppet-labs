from __future__ import annotations

from eval.models import DriftReport, EvalResult, EvalRun, MetricDelta

DRIFT_WARN_THRESHOLD = -0.02


def compute_drift(
    run_a: EvalRun,
    results_a: list[EvalResult],
    run_b: EvalRun,
    results_b: list[EvalResult],
) -> DriftReport:
    map_a = {r.case_id: r for r in results_a}
    map_b = {r.case_id: r for r in results_b}

    only_a = len(set(map_a) - set(map_b))
    only_b = len(set(map_b) - set(map_a))

    # Top-level metrics
    top_metrics = [
        _delta("mean_score", run_a.mean_score, run_b.mean_score),
        _delta("refusal_rate", run_a.refusal_rate, run_b.refusal_rate),
    ]

    # Per-rubric deltas
    rubric_names = _collect_rubric_names(results_a, results_b)
    rubric_deltas: dict[str, list[MetricDelta]] = {}
    for rname in rubric_names:
        mean_a = _mean_rubric_score(results_a, rname)
        mean_b = _mean_rubric_score(results_b, rname)
        rubric_deltas[rname] = [_delta("mean_score", mean_a, mean_b)]

    # Per-dataset deltas
    dataset_prefixes = _collect_prefixes(results_a, results_b)
    dataset_deltas: dict[str, list[MetricDelta]] = {}
    for prefix in dataset_prefixes:
        mean_a = _mean_score_for_prefix(results_a, prefix)
        mean_b = _mean_score_for_prefix(results_b, prefix)
        dataset_deltas[prefix] = [_delta("mean_score", mean_a, mean_b)]

    # Flip detection on intersection
    intersection = set(map_a) & set(map_b)
    new_failures: list[str] = []
    new_passes: list[str] = []
    for case_id in intersection:
        ra, rb = map_a[case_id], map_b[case_id]
        passed_a = _is_pass(ra)
        passed_b = _is_pass(rb)
        if passed_a and not passed_b:
            new_failures.append(case_id)
        elif not passed_a and passed_b:
            new_passes.append(case_id)

    return DriftReport(
        run_a_id=run_a.id,
        run_b_id=run_b.id,
        run_a_label=run_a.config.run_label,
        run_b_label=run_b.config.run_label,
        cases_in_a_only=only_a,
        cases_in_b_only=only_b,
        metrics=top_metrics,
        rubric_deltas=rubric_deltas,
        dataset_deltas=dataset_deltas,
        new_failures=sorted(new_failures),
        new_passes=sorted(new_passes),
    )


def format_drift_report(report: DriftReport, use_color: bool = True) -> str:
    import io

    from rich.console import Console
    from rich.table import Table

    buf = io.StringIO()
    console = Console(file=buf, no_color=not use_color, highlight=False)

    a_label = report.run_a_label or report.run_a_id[:8]
    b_label = report.run_b_label or report.run_b_id[:8]
    console.print(f"\n[bold]Drift Report:[/bold] {a_label} (baseline) → {b_label} (current)")
    if report.cases_in_a_only or report.cases_in_b_only:
        console.print(
            f"  [dim]{report.cases_in_a_only} case(s) in baseline only, "
            f"{report.cases_in_b_only} case(s) in current only (excluded from flip detection)[/dim]"
        )

    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("Delta", justify="right")

    for m in report.metrics:
        table.add_row(m.metric, _fmt(m.run_a_value), _fmt(m.run_b_value), _fmt_delta(m))
    console.print(table)

    if report.rubric_deltas:
        console.print("[bold]By rubric:[/bold]")
        rt = Table(show_header=True, header_style="bold")
        rt.add_column("Rubric", style="cyan")
        rt.add_column("Baseline", justify="right")
        rt.add_column("Current", justify="right")
        rt.add_column("Delta", justify="right")
        for rname, metrics in report.rubric_deltas.items():
            for m in metrics:
                warn = " [yellow]⚠[/yellow]" if (m.delta or 0) < DRIFT_WARN_THRESHOLD else ""
                rt.add_row(rname, _fmt(m.run_a_value), _fmt(m.run_b_value), _fmt_delta(m) + warn)
        console.print(rt)

    if report.dataset_deltas:
        console.print("[bold]By dataset:[/bold]")
        dt = Table(show_header=True, header_style="bold")
        dt.add_column("Dataset", style="cyan")
        dt.add_column("Baseline", justify="right")
        dt.add_column("Current", justify="right")
        dt.add_column("Delta", justify="right")
        for dname, metrics in report.dataset_deltas.items():
            for m in metrics:
                dt.add_row(dname, _fmt(m.run_a_value), _fmt(m.run_b_value), _fmt_delta(m))
        console.print(dt)

    console.print(
        f"[bold]Case flips:[/bold] "
        f"[red]{len(report.new_failures)} new failure(s)[/red], "
        f"[green]{len(report.new_passes)} new pass(es)[/green]"
    )
    if report.new_failures:
        console.print(
            f"  Failures: {', '.join(report.new_failures[:10])}"
            + (" ..." if len(report.new_failures) > 10 else "")
        )
    if report.new_passes:
        console.print(
            f"  Passes:   {', '.join(report.new_passes[:10])}"
            + (" ..." if len(report.new_passes) > 10 else "")
        )

    return buf.getvalue()


# ── Private helpers ────────────────────────────────────────────────────────────


def _delta(metric: str, a: float | None, b: float | None) -> MetricDelta:
    if a is not None and b is not None:
        d = b - a
    else:
        d = None
    return MetricDelta(
        metric=metric, run_a_value=a, run_b_value=b, delta=d, direction=_direction(d)
    )


def _direction(delta: float | None) -> str:
    if delta is None:
        return "unknown"
    if delta > 0.001:
        return "up"
    if delta < -0.001:
        return "down"
    return "unchanged"


def _is_pass(result: EvalResult) -> bool:
    score_ok = (result.aggregate_score or 0.0) >= 0.5
    refusal_ok = result.refusal_detected == result.expect_refusal
    return score_ok and refusal_ok


def _collect_rubric_names(a: list[EvalResult], b: list[EvalResult]) -> set[str]:
    names: set[str] = set()
    for results in (a, b):
        for r in results:
            for cs in r.criterion_scores:
                names.add(cs.rubric_name)
    return names


def _mean_rubric_score(results: list[EvalResult], rubric_name: str) -> float | None:
    scores = [
        cs.score
        for r in results
        for cs in r.criterion_scores
        if cs.rubric_name == rubric_name and cs.score is not None
    ]
    return sum(scores) / len(scores) if scores else None


def _collect_prefixes(a: list[EvalResult], b: list[EvalResult]) -> set[str]:
    prefixes: set[str] = set()
    for results in (a, b):
        for r in results:
            prefix = r.case_id.split(":")[0]
            prefixes.add(prefix)
    return prefixes


def _mean_score_for_prefix(results: list[EvalResult], prefix: str) -> float | None:
    scores = [
        r.aggregate_score
        for r in results
        if r.case_id.startswith(prefix + ":") and r.aggregate_score is not None
    ]
    return sum(scores) / len(scores) if scores else None


def _fmt(v: float | None) -> str:
    return f"{v:.3f}" if v is not None else "—"


def _fmt_delta(m: MetricDelta) -> str:
    if m.delta is None:
        return "—"
    arrow = {"up": "↑", "down": "↓", "unchanged": "→", "unknown": "?"}.get(m.direction, "")
    sign = "+" if m.delta > 0 else ""
    return f"{sign}{m.delta:.3f} {arrow}"
