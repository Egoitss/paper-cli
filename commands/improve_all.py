from __future__ import annotations
import click
import config
from rich.console import Console
from commands.improve import run_improve_section
from commands.summary import run_summary

console = Console()


@click.command("improve-all")
@click.option("--summary/--no-summary", "regen_summary", default=True,
              help="Regenerate summary_document.docx after all sections (default: on).")
def improve_all(regen_summary: bool) -> None:
    """Run targeted + master improvement passes over every drafted chapter, then regenerate the summary.

    Applies the same two passes as `improve --targeted --master` for each section.
    Use `improve --section X` directly for humanize or condense passes.
    """
    improved: list[str] = []
    skipped: list[str] = []

    for section in config.SECTIONS:
        path = config.CHAPTERS_DIR / f"{section}.md"
        if not path.exists():
            skipped.append(section)
            continue
        console.print(f"\n[bold cyan]── {section} ──[/bold cyan]")
        run_improve_section(
            section,
            targeted=True,
            only=None,
            master=True,
            humanize=False,
            style=None,
            condense=False,
        )
        improved.append(section)

    console.print(f"\n[green]Improved {len(improved)} section(s).[/green]")
    if skipped:
        console.print(f"[dim]Skipped (no draft): {', '.join(skipped)}[/dim]")

    if regen_summary and improved:
        console.print("\n[bold]Regenerating summary document…[/bold]")
        output = str(config.PAPER_DIR / "summary_document.docx")
        run_summary(output)
