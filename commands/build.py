from __future__ import annotations
import json
import click
import config
from pathlib import Path
from rich.console import Console
from core.state_manager import get_approved_sections
from formatters.docx_builder import build_document

console = Console()


@click.command()
@click.option("--output", default=None,
              help="Output .docx path (default: papers/<name>/submission_draft.docx)")
def build(output: str) -> None:
    """Assemble all approved chapters into a submission-ready .docx file."""
    if output is None:
        output = str(config.PAPER_DIR / "submission_draft.docx")

    # citations.json must exist — it is produced by `paper cite`
    citations_path = config.DATA_DIR / "citations.json"
    if not citations_path.exists():
        console.print("[red]citations.json not found. Run `paper cite` first.[/red]")
        raise SystemExit(1)

    citations = json.loads(citations_path.read_text(encoding="utf-8"))

    # Load only approved sections, in the canonical order defined by config.SECTIONS
    approved = get_approved_sections()
    chapters: dict[str, str] = {}
    for section in config.SECTIONS:
        if section not in approved:
            console.print(f"[yellow]Skipping unapproved section:[/yellow] {section}")
            continue
        path = config.CHAPTERS_DIR / f"{section}.md"
        if path.exists():
            chapters[section] = path.read_text(encoding="utf-8")

    if not chapters:
        console.print("[red]No approved chapters found.[/red]")
        raise SystemExit(1)

    # Collect appendices appendix_1.md … appendix_5.md if they exist
    appendices: dict[str, str] = {}
    if config.APPENDICES_DIR.exists():
        for i in range(1, 6):
            apath = config.APPENDICES_DIR / f"appendix_{i}.md"
            if apath.exists():
                appendices[f"appendix_{i}"] = apath.read_text(encoding="utf-8")

    console.print(f"[bold]Building document[/bold] with {len(chapters)} sections...")
    doc = build_document(chapters, citations, appendices)

    out_path = Path(output)
    doc.save(str(out_path))
    console.print(f"[green]Saved:[/green] {out_path}")
    console.print("[dim]Tip: Open in Word and update the Table of Contents field (F9).[/dim]")
