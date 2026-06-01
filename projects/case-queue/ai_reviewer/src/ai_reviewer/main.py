from __future__ import annotations

import asyncio
import signal
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from ai_reviewer.classifier import classify_with_claude, classify_with_ollama
from ai_reviewer.client import CaseQueueClient
from ai_reviewer.config import settings
from ai_reviewer.models import CaseDetail

app = typer.Typer(help="AI-powered case reviewer for the case-queue trust & safety tool.")
console = Console()
err_console = Console(stderr=True)

_BACKEND_CHOICES = ["ollama", "claude"]

# Claude cost guardrail: haiku-4-5 ~$0.80/MTok input + $4.00/MTok output
# ~500 input tokens + ~100 output tokens per case
_CLAUDE_COST_PER_CASE = 0.0008  # USD


def _confirm_claude_run(max_cases: int) -> bool:
    estimated = max_cases * _CLAUDE_COST_PER_CASE
    console.print("\n[bold yellow]⚠ Claude backend selected[/bold yellow]")
    console.print(f"  Model:           [cyan]{settings.claude_model}[/cyan]")
    console.print(f"  Max cases / run: [cyan]{max_cases}[/cyan]")
    console.print(f"  Estimated cost:  [cyan]~${estimated:.4f} USD per poll cycle[/cyan]")
    console.print("  [dim](~$0.0008 per case, based on 500 input + 100 output tokens)[/dim]\n")
    return typer.confirm("Proceed with Claude backend?", default=False)


async def _classify_case(
    case: CaseDetail,
    backend: str,
) -> tuple[str, str, float, str]:
    """Returns (action, reasoning, confidence, backend_used)."""
    if backend == "claude":
        result = await classify_with_claude(
            case,
            model=settings.claude_model,
            confidence_threshold=settings.confidence_threshold,
        )
    else:
        result = await classify_with_ollama(
            case,
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            confidence_threshold=settings.confidence_threshold,
        )
    return result.action, result.reasoning, result.confidence, backend


def _action_style(action: str) -> str:
    return {
        "approve": "[green]approve[/green]",
        "reject": "[red]reject[/red]",
        "escalate": "[yellow]escalate[/yellow]",
    }.get(action, action)


async def _poll_once(
    client: CaseQueueClient,
    backend: str,
    batch_size: int,
    dry_run: bool,
    claude_cases_used: list[int],
    claude_max: int,
) -> None:
    page = await client.fetch_pending_cases(page_size=batch_size)

    if page.total == 0:
        console.print("[dim]  No pending cases.[/dim]")
        return

    cases_to_process = page.items
    if backend == "claude" and claude_max > 0:
        remaining = claude_max - claude_cases_used[0]
        if remaining <= 0:
            console.print(
                f"[yellow]  Claude cap reached ({claude_max} cases). Skipping this cycle.[/yellow]"
            )
            return
        cases_to_process = cases_to_process[:remaining]

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Case ID", style="dim", width=10)
    table.add_column("Category", width=14)
    table.add_column("Sev", width=6)
    table.add_column("Decision", width=10)
    table.add_column("Conf", width=6)
    table.add_column("Reasoning")

    processed = 0
    for item in cases_to_process:
        detail = await client.fetch_case_detail(item.id)
        action, reasoning, confidence, _ = await _classify_case(detail, backend)

        short_id = item.id[:8]
        table.add_row(
            short_id,
            item.category.replace("_", " "),
            item.severity,
            _action_style(action),
            f"{confidence:.0%}",
            reasoning[:80] + ("…" if len(reasoning) > 80 else ""),
        )

        if not dry_run:
            await client.post_decision(item.id, action, reasoning)

        if backend == "claude":
            claude_cases_used[0] += 1
        processed += 1

    console.print(table)
    if dry_run:
        console.print("[dim]  Dry run — no decisions posted.[/dim]")


@app.command()
def run(  # noqa: PLR0913
    backend: str = settings.backend,
    max_cases: int = settings.claude_max_cases,
    interval: int = settings.poll_interval,
    batch_size: int = settings.batch_size,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Classify without posting")] = False,
    api_url: str = settings.api_url,
    actor_id: str = settings.actor_id,
    actor_role: str = settings.actor_role,
) -> None:
    """Start the AI case reviewer polling loop."""
    if backend not in _BACKEND_CHOICES:
        err_console.print(f"[red]Unknown backend '{backend}'. Choose: {_BACKEND_CHOICES}[/red]")
        raise typer.Exit(1)

    if backend == "claude":
        if not _confirm_claude_run(max_cases if max_cases > 0 else batch_size):
            console.print("Aborted.")
            raise typer.Exit(0)

    console.print("\n[bold]Case Reviewer[/bold]")
    cost_note = "  ⚠ costs money" if backend == "claude" else ""
    console.print(f"  Backend:    [cyan]{backend}[/cyan]{cost_note}")
    console.print(f"  API:        [cyan]{api_url}[/cyan]")
    console.print(f"  Actor:      [cyan]{actor_id}[/cyan] / [cyan]{actor_role}[/cyan]")
    console.print(f"  Interval:   [cyan]{interval}s[/cyan]")
    threshold_pct = f"{settings.confidence_threshold:.0%}"
    console.print(f"  Threshold:  [cyan]{threshold_pct}[/cyan] confidence to decide")
    if dry_run:
        console.print("  [bold yellow]DRY RUN — decisions will not be posted[/bold yellow]")
    console.print()

    client = CaseQueueClient(api_url, actor_id, actor_role)
    claude_cases_used = [0]  # mutable counter shared across cycles

    stop = asyncio.Event()

    def _handle_signal(*_: object) -> None:
        console.print("\n[dim]Stopping…[/dim]")
        stop.set()

    async def _loop() -> None:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _handle_signal)

        cycle = 0
        while not stop.is_set():
            cycle += 1
            console.rule(f"[dim]Poll #{cycle}[/dim]")
            try:
                await _poll_once(
                    client, backend, batch_size, dry_run, claude_cases_used, max_cases
                )
                if backend == "claude" and max_cases > 0:
                    console.print(
                        f"[dim]  Claude cases used: {claude_cases_used[0]} / {max_cases}[/dim]"
                    )
            except Exception as exc:
                err_console.print(f"[red]  Error in poll cycle: {exc}[/red]")

            if not stop.is_set():
                console.print(f"[dim]  Sleeping {interval}s…[/dim]")
                try:
                    await asyncio.wait_for(stop.wait(), timeout=interval)
                except TimeoutError:
                    pass

        console.print("[bold]Reviewer stopped.[/bold]")

    asyncio.run(_loop())
