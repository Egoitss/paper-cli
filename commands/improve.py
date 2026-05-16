from __future__ import annotations
import click
import config
from pathlib import Path
from rich.console import Console
from core.api_client import call
from core.state_manager import mark_drafted

console = Console()

_TARGETED_ISSUES: list[tuple[str, str]] = [
    ("syntactic_variance",
     "Revise the text to introduce natural syntactic variation. Vary sentence length and "
     "structure, mix shorter and longer sentences, and diversify sentence openings. "
     "Maintain an academic tone, but reduce mechanical uniformity."),

    ("synonym_redundancy",
     "Reduce redundant synonyms and wordiness. Where multiple words convey the same meaning, "
     "keep only the most precise one. Prioritize clarity and specificity over stylistic inflation."),

    ("templated_structure",
     "Revise the text to avoid overly templated or formulaic organisation. Restructure sections "
     "that follow a predictable, mechanical pattern so they read as a coherent analytical "
     "argument rather than a series of boxes being ticked."),

    ("shallow_analysis",
     "Deepen the analysis. Go beyond describing facts or rules by explaining their significance, "
     "implications, and practical consequences. Add brief interpretive or critical insights "
     "where appropriate."),

    ("vague_generalizations",
     "Replace broad generalizations with more precise and specific statements. Where possible, "
     "include concrete aspects, conditions, or examples that clarify the claim."),

    ("superficial_sources",
     "Strengthen how sources are used by integrating them into the argument. Instead of only "
     "reporting what a source says, explain how it supports, refines, or challenges the point "
     "being made."),

    ("mechanical_citation",
     "Integrate references more tightly into the text by explicitly linking each citation to a "
     "specific claim or inference. Briefly clarify what the cited source contributes to the "
     "argument."),

    ("checklist_structure",
     "Convert list-like or checklist structures into a more fluid analytical narrative. Preserve "
     "the logical order, but connect points through explanation and transitions rather than "
     "isolated statements."),

    ("terminological_precision",
     "Increase terminological precision by using domain-appropriate concepts where relevant. "
     "Replace overly generic wording with more specific, technically accurate terms."),

    ("sterile_tone",
     "Maintain an academic tone while introducing a subtle analytical voice. Where appropriate, "
     "include restrained interpretive positioning rather than fully neutral, impersonal phrasing."),

    ("methodology_inflation",
     "Streamline the methodology section by focusing only on the most relevant methods. Briefly "
     "explain how each method is applied, avoiding generic or inflated lists."),

    ("rigid_transitions",
     "Make transitions between sections more natural and less formulaic. Avoid explicit structural "
     "signposting where possible, while preserving logical continuity."),
]

_ISSUE_IDS = [k for k, _ in _TARGETED_ISSUES]

_MASTER_PROMPT = (
    "Revise the text to reduce mechanical patterns and improve natural academic style. "
    "Introduce variation in sentence structure and length, eliminate redundant synonyms, "
    "and avoid overly templated organisation. Deepen the analysis by adding interpretation, "
    "implications, and concrete detail where appropriate. Integrate sources into the argument "
    "by explaining their relevance rather than merely citing them. Replace checklist-style "
    "sections with a more fluid analytical narrative. Increase terminological precision and "
    "introduce a subtle authorial perspective while maintaining academic objectivity. "
    "Streamline methodology mentions — explain only the most relevant methods and how they "
    "are applied. Replace broad generalisations with more precise and specific statements."
)


def _build_system() -> str:
    return (
        f"<system>\n"
        f"  <role>You are an expert academic editor specialising in {config.PAPER_DOMAIN}. "
        f"You revise academic texts to improve style, depth, and argumentation without "
        f"changing the substance, sources, or citation markers.</role>\n"
        f"  <rules>\n"
        f"    <rule>Preserve every {{{{cite:SOURCE_ID:PAGE}}}} marker exactly — do not alter, "
        f"move, or remove them.</rule>\n"
        f"    <rule>Preserve all Markdown headings (##, ###) exactly.</rule>\n"
        f"    <rule>Do not add new claims or sources not present in the original.</rule>\n"
        f"    <rule>Do NOT use em dashes (—). Use commas, periods, or restructure instead.</rule>\n"
        f"    <rule>Write in formal third-person academic English.</rule>\n"
        f"    <rule>Return only the revised text — no commentary, no preamble.</rule>\n"
        f"  </rules>\n"
        f"</system>"
    )


def _build_targeted_prompt(draft: str, instructions: list[str]) -> str:
    combined = " ".join(instructions)
    return (
        f"<user>\n"
        f"  <task>Apply these writing improvements to the academic text below:\n"
        f"  {combined}</task>\n"
        f"  <text>{draft}</text>\n"
        f"</user>"
    )


def _build_master_prompt(draft: str) -> str:
    return (
        f"<user>\n"
        f"  <task>{_MASTER_PROMPT}</task>\n"
        f"  <text>{draft}</text>\n"
        f"</user>"
    )


def _build_humanize_prompt(draft: str, sample: str) -> str:
    return (
        f"<user>\n"
        f"  <task>Revise the academic text below to match the writing style of the provided "
        f"sample. Adopt the sentence rhythm, paragraph structure, vocabulary register, and "
        f"analytical voice from the sample. Do not copy content from the sample — only adapt "
        f"the style. Preserve all {{{{cite:SOURCE_ID:PAGE}}}} markers and Markdown headings "
        f"exactly. Return only the revised text.</task>\n"
        f"  <style_sample>{sample}</style_sample>\n"
        f"  <text>{draft}</text>\n"
        f"</user>"
    )


def _build_condense_prompt(draft: str, target_words: int) -> str:
    return (
        f"<user>\n"
        f"  <task>Condense this academic text to approximately {target_words} words. "
        f"Preserve the improved academic style: syntactic variation, analytical depth, "
        f"integrated source use, and fluid narrative structure. Cut redundant elaboration, "
        f"excessive examples, and inflated phrasing — but keep every key argument and "
        f"all {{{{cite:SOURCE_ID:PAGE}}}} markers exactly as they are. "
        f"Do not add new content. Return only the condensed text.</task>\n"
        f"  <text>{draft}</text>\n"
        f"</user>"
    )


def _resolve_issues(only: str | None) -> list[tuple[str, str]]:
    """Return the subset of _TARGETED_ISSUES requested via --only, or all if not set."""
    if not only:
        return _TARGETED_ISSUES
    selected: list[tuple[str, str]] = []
    for token in only.split(","):
        token = token.strip()
        if token.isdigit():
            idx = int(token) - 1
            if 0 <= idx < len(_TARGETED_ISSUES):
                selected.append(_TARGETED_ISSUES[idx])
            else:
                console.print(
                f"[yellow]Issue number {token} out of range "
                f"(1-{len(_TARGETED_ISSUES)}), skipping.[/yellow]"
            )
        elif token in _ISSUE_IDS:
            selected.append(next(item for item in _TARGETED_ISSUES if item[0] == token))
        else:
            console.print(f"[yellow]Unknown issue id '{token}', skipping.[/yellow]")
    return selected


def _apply_improvement_passes(
    text: str,
    system: str,
    section: str,
    targeted: bool,
    only: str | None,
    master: bool,
    humanize: bool,
    style: str | None,
    condense: bool,
) -> str:
    if targeted:
        issues = _resolve_issues(only)
        if issues:
            labels = ", ".join(k for k, _ in issues)
            console.print(f"[dim]Targeted pass ({len(issues)} issues): {labels}…[/dim]")
            text = call(system, _build_targeted_prompt(text, [d for _, d in issues]), mode="write")
        else:
            console.print("[yellow]No valid issues selected — skipping targeted pass.[/yellow]")

    if master:
        console.print("[dim]Master refinement pass…[/dim]")
        text = call(system, _build_master_prompt(text), mode="write")

    if humanize:
        sample_path = Path(style)
        if not sample_path.exists():
            console.print(f"[red]Style sample not found:[/red] {style}")
            raise SystemExit(1)
        console.print(f"[dim]Humanize pass (sample: {sample_path.name})…[/dim]")
        text = call(system, _build_humanize_prompt(text, sample_path.read_text(encoding="utf-8")), mode="write")

    if condense:
        min_w, max_w = config.SECTION_META[section]["target_words"]
        target = (min_w + max_w) // 2
        console.print(f"[dim]Condense pass (~{target} words)…[/dim]")
        text = call(system, _build_condense_prompt(text, target), mode="write")

    return text


def run_improve_section(
    section: str,
    targeted: bool = True,
    only: str | None = None,
    master: bool = True,
    humanize: bool = False,
    style: str | None = None,
    condense: bool = False,
) -> None:
    """Core logic to improve a section.

    Assumes section exists in config.SECTIONS (validation is the caller's responsibility).
    """
    path = config.CHAPTERS_DIR / f"{section}.md"
    if not path.exists():
        console.print(f"[red]No draft found for section:[/red] {section}")
        raise SystemExit(1)

    if humanize and not style:
        console.print("[red]--humanize requires --style <path-to-sample-file>.[/red]")
        raise SystemExit(1)

    if not targeted and not master and not humanize and not condense:
        console.print("[yellow]Nothing to do — all passes disabled.[/yellow]")
        raise SystemExit(0)

    draft = path.read_text(encoding="utf-8")
    word_count_before = len(draft.split())
    console.print(f"[bold]Improving:[/bold] {config.SECTION_META[section]['title']} "
                  f"({word_count_before} words)")

    text = _apply_improvement_passes(
        draft, _build_system(), section,
        targeted, only, master, humanize, style, condense,
    )

    path.write_text(text, encoding="utf-8")
    word_count_after = len(text.split())
    delta = word_count_after - word_count_before
    sign = "+" if delta >= 0 else ""
    console.print(f"[green]Saved:[/green] {path}")
    console.print(f"[dim]Words: {word_count_before} → {word_count_after} ({sign}{delta})[/dim]")
    console.print("[dim]Review the changes, then re-approve in project_state.md.[/dim]")
    mark_drafted(section)


@click.command()
@click.option("--section", required=True,
              help="Section ID to improve (e.g. part_1, introduction).")
@click.option("--targeted/--no-targeted", default=True,
              help="Apply targeted improvement prompts (default: on).")
@click.option("--only", default=None,
              help="Comma-separated issue IDs or numbers (1-12) to run instead of all. "
                   f"IDs: {', '.join(_ISSUE_IDS)}")
@click.option("--master/--no-master", default=True,
              help="Apply master refinement prompt after targeted pass (default: on).")
@click.option("--humanize", is_flag=True, default=False,
              help="Apply a style-mimicry pass using a writing sample.")
@click.option("--style", default=None,
              help="Path to a writing sample file for --humanize.")
@click.option("--condense", is_flag=True, default=False,
              help="Condense to section's target word count after other passes.")
def improve(section: str, targeted: bool, only: str | None,
            master: bool, humanize: bool, style: str | None, condense: bool) -> None:
    """Improve the writing quality of a drafted section.

    \b
    Targeted issue IDs (use with --only):
      1.  syntactic_variance       9.  terminological_precision
      2.  synonym_redundancy       10. sterile_tone
      3.  templated_structure      11. methodology_inflation
      4.  shallow_analysis         12. rigid_transitions
      5.  vague_generalizations
      6.  superficial_sources
      7.  mechanical_citation
      8.  checklist_structure
    """
    if section not in config.SECTIONS:
        console.print(f"[red]Unknown section:[/red] {section}")
        console.print(f"Available: {', '.join(config.SECTIONS)}")
        raise SystemExit(1)
    run_improve_section(section, targeted, only, master, humanize, style, condense)
