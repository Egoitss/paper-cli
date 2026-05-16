from __future__ import annotations
import json
import click
import config
from rich.console import Console
from core.source_manager import load_sources
from core.state_manager import get_approved_sections
from formatters.footnotes import assign_footnote_numbers, replace_markers, extract_abbreviations
from formatters.bibliography import format_source, sort_bibliography

console = Console()


def _load_approved_chapters() -> dict[str, str]:
    approved = get_approved_sections()
    chapters: dict[str, str] = {}
    for section in config.SECTIONS:
        if section not in approved:
            continue
        path = config.CHAPTERS_DIR / f"{section}.md"
        if path.exists():
            chapters[section] = path.read_text(encoding="utf-8")
    return chapters


def _write_chapters_and_collect(
    chapters: dict[str, str], numbered: dict[str, list[dict]]
) -> list[dict]:
    # Replaces {{cite:...}} markers in each chapter file with superscripts,
    # then collects the flat ordered list of footnotes for citations.json
    footnotes: list[dict] = []
    for section_id in config.SECTIONS:
        citations = numbered.get(section_id, [])
        if not citations:
            continue
        text = chapters[section_id]
        mapping = {c["marker"]: c["number"] for c in citations}
        (config.CHAPTERS_DIR / f"{section_id}.md").write_text(
            replace_markers(text, mapping), encoding="utf-8"
        )
        for c in citations:
            footnotes.append({
                "number": c["number"],
                "source_id": c["source_id"],
                "page": c["page"],
                "section": section_id,
            })
    return footnotes


def _build_citations_output(
    footnotes: list[dict], sources: list[dict], all_text: str
) -> dict:
    # Builds the complete citations.json payload: ordered footnotes, formatted bibliography,
    # and a sorted list of abbreviations found across all chapter text
    source_map = {s["id"]: s for s in sources}
    used_ids = list(dict.fromkeys(fn["source_id"] for fn in footnotes))
    used_sources = [source_map[sid] for sid in used_ids if sid in source_map]
    bibliography = [
        {"id": s["id"], "formatted": format_source(s)}
        for s in sort_bibliography(used_sources)
    ]
    return {
        "footnotes": footnotes,
        "bibliography": bibliography,
        "abbreviations": extract_abbreviations(all_text),
    }


@click.command()
def cite() -> None:
    """Assign sequential footnote numbers and build bibliography."""
    chapters = _load_approved_chapters()
    if not chapters:
        console.print("[red]No approved sections found. Approve sections in project_state.md first.[/red]")
        return

    numbered = assign_footnote_numbers(chapters)
    if sum(len(v) for v in numbered.values()) == 0:
        console.print(
            "[yellow]Warning: no {{cite:...}} markers found in approved chapters.[/yellow]\n"
            "[yellow]If you have already run `paper cite`, markers have been replaced with "
            "superscripts and cannot be re-processed. Citations.json was NOT updated.[/yellow]"
        )
        return

    footnotes = _write_chapters_and_collect(chapters, numbered)
    output = _build_citations_output(footnotes, load_sources(), "\n".join(chapters.values()))
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    (config.DATA_DIR / "citations.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    console.print(f"[green]Citations written:[/green] {len(output['footnotes'])} footnotes")
    console.print(f"[green]Bibliography entries:[/green] {len(output['bibliography'])}")
    n = len(output["abbreviations"])
    if n >= 7:
        console.print(f"[green]Abbreviations found ({n}) — list will be included.[/green]")
    else:
        console.print(f"[dim]Abbreviations found ({n}) — below 7, list omitted.[/dim]")
