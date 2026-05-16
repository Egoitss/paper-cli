from __future__ import annotations
import click
import config
from rich.console import Console
from rich.panel import Panel
from core.api_client import call
from core.prompt_builder import build_system, build_write_prompt
from core.source_manager import load_sources
from core.state_manager import mark_drafted
from commands.evaluate import evaluate, EvalResult

console = Console()
MAX_RETRIES = 3


def _generate_draft(section: str, sources_to_use: list[str]) -> str:
    # System block is cached because it rarely changes between retries
    system = build_system(include_sources=True)
    user = build_write_prompt(section, sources_to_use)
    return call(system=system, user=user, mode="write", use_cache=True)


def _pick_sources(section: str) -> list[str]:
    # Selects up to 5 sources, prioritised by type based on what kind of section is being written;
    # empirical sections favour industry reports, theoretical sections favour scientific papers
    sources = load_sources()
    meta = config.SECTION_META[section]
    kind = meta["kind"]
    type_priority = {
        "introduction": ["scientific", "general", "industry", "legal"],
        "empirical": ["industry", "scientific", "general", "legal"],
        "conclusions": ["scientific", "industry", "general", "legal"],
        "subchapter": ["scientific", "general", "industry", "legal"],
    }.get(kind, ["scientific", "general", "industry", "legal"])

    selected: list[str] = []
    for t in type_priority:
        for s in sources:
            if s.get("type") == t and s["id"] not in selected:
                selected.append(s["id"])
            if len(selected) >= 5:
                break
        if len(selected) >= 5:
            break
    # Fall back to first 5 sources if no typed sources exist
    return selected or [s["id"] for s in sources[:5]]


@click.command()
@click.option("--section", required=True, help="Section ID to write (e.g. chapter_1_1).")
def write(section: str) -> None:
    """Draft a paper section using Claude API, auto-evaluate before saving."""
    if section not in config.SECTIONS:
        raise click.UsageError(f"Unknown section '{section}'. Valid: {', '.join(config.SECTIONS)}")

    meta = config.SECTION_META[section]
    console.print(Panel(f"Writing: [bold]{meta['title']}[/bold]", expand=False))

    sources_to_use = _pick_sources(section)
    draft = ""
    result: EvalResult | None = None

    # Generate → evaluate → retry up to MAX_RETRIES times
    for attempt in range(1, MAX_RETRIES + 1):
        console.print(f"[dim]Attempt {attempt}/{MAX_RETRIES}[/dim]")
        draft = _generate_draft(section, sources_to_use)
        result = evaluate(section, draft)

        if result.passed:
            console.print(f"[green]Evaluation passed[/green] ({result.word_count} words)")
            break

        console.print(f"[yellow]Evaluation failed (attempt {attempt}):[/yellow]")
        for f in result.failures:
            console.print(f"  • {f['criterion']}: {f['detail']}")

    # Always save the draft, even if all evaluation attempts failed,
    # so the user has something to review rather than losing the work
    config.CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.CHAPTERS_DIR / f"{section}.md"
    path.write_text(draft, encoding="utf-8")
    mark_drafted(section)

    if result and not result.passed:
        console.print("[yellow]Warning: saved after max retries — manual review recommended.[/yellow]")

    console.print(f"[bold]Saved:[/bold] {path}")
    console.print("Mark as approved in project_state.md when satisfied.")
