from __future__ import annotations

import json
import click
from rich.console import Console
from core.api_client import call_with_tools
from core.prompt_builder import build_research_prompt, build_system
from core.source_manager import add_source, get_source_count, load_sources, check_distribution
import config

console = Console()

# Anthropic web search tool definition — uses the native search capability
_WEB_SEARCH_TOOL = [{"type": "web_search_20250305", "name": "web_search"}]


def _search(query: str, source_type: str, existing_urls: list) -> str:
    system = build_system(include_sources=False)
    user = build_research_prompt(query, source_type, existing_urls)
    return call_with_tools(system=system, user=user, tools=_WEB_SEARCH_TOOL)


def _parse_sources(raw: str) -> list:
    # The model may wrap the JSON array in prose; this finds the outermost `[…]`
    # by scanning backwards from the last `]` to its matching `[`
    end = raw.rfind("]")
    if end == -1:
        return []

    depth = 0
    for i in range(end, -1, -1):
        if raw[i] == "]":
            depth += 1
        elif raw[i] == "[":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[i : end + 1])
                except json.JSONDecodeError:
                    return []

    return []


def _save_appendix_material(source: dict, index: int) -> None:
    # Writes key quotes to an appendix file on first encounter only;
    # capped at appendix_5 to stay within the submission limit
    config.APPENDICES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.APPENDICES_DIR / f"appendix_{index}.md"
    if not path.exists() and source.get("key_quotes"):
        content = f"# Appendix {index}: Data from {source['title']}\n\n"
        content += f"**Source:** {source.get('author') or source['title']} ({source['year']})\n\n"
        for q in source["key_quotes"]:
            content += f"- {q}\n"
        path.write_text(content, encoding="utf-8")


@click.command()
@click.argument("query")
@click.option(
    "--type", "source_type",
    type=click.Choice(["scientific", "legal", "industry", "general"]),
    default="general",
    show_default=True,
    help="Type of source to search for.",
)
def research(query: str, source_type: str) -> None:
    """Search for sources and add them to sources.json."""
    existing_urls = [s["url"] for s in load_sources()]
    console.print(f"[bold]Searching:[/bold] {query} [dim](type: {source_type})[/dim]")

    raw = _search(query, source_type, existing_urls)
    found = _parse_sources(raw)

    if not found:
        console.print("[yellow]No sources parsed from response.[/yellow]")
        return

    # Add new sources, skip duplicates, and save appendix material for data-rich sources
    added = 0
    appendix_index = len(list(config.APPENDICES_DIR.glob("appendix_*.md"))) + 1
    for src in found:
        before = get_source_count()
        add_source(src)
        if get_source_count() > before:
            console.print(f"[green]Added:[/green] {src['title']} ({src['year']})")
            if source_type in ("scientific", "industry") and appendix_index <= 5:
                _save_appendix_material(src, appendix_index)
                appendix_index += 1
            added += 1
        else:
            console.print(f"[dim]Skipped (duplicate):[/dim] {src['title']}")

    console.print(f"\n[bold]Total sources:[/bold] {get_source_count()}/{config.TOTAL_SOURCES_TARGET}")

    # Warn if mandatory source type minimums are not yet met
    dist = check_distribution()
    if dist["warnings"]:
        for w in dist["warnings"]:
            console.print(f"[yellow]Warning:[/yellow] {w}")
    else:
        console.print("[green]Source distribution requirements met.[/green]")
