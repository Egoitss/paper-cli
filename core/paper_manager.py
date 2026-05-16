from __future__ import annotations
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).parent.parent
PAPERS_DIR = BASE_DIR / "papers"
ACTIVE_PAPER_FILE = BASE_DIR / ".active_paper"


def get_active_paper_name() -> str | None:
    if ACTIVE_PAPER_FILE.exists():
        name = ACTIVE_PAPER_FILE.read_text(encoding="utf-8").strip()
        return name or None
    return None


def load_paper_yaml(name: str) -> dict:
    path = PAPERS_DIR / name / "paper.yaml"
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Paper '{name}' has no paper.yaml at {path}") from None
    except yaml.YAMLError as exc:
        raise ValueError(f"paper.yaml for '{name}' is not valid YAML: {exc}") from exc


def _parse_paper(name: str, raw: dict) -> dict:
    sections_list = [s["id"] for s in raw["sections"]]
    section_meta: dict[str, dict] = {}
    for s in raw["sections"]:
        meta = {k: v for k, v in s.items() if k != "id"}
        meta["target_words"] = tuple(meta["target_words"])
        section_meta[s["id"]] = meta
    chapter_headings = {int(k): v for k, v in raw.get("chapter_headings", {}).items()}
    features: dict[str, bool] = {"bibliography": True, "appendices": True, "require_scientific": True}
    features.update(raw.get("features", {}))
    paper_dir = PAPERS_DIR / name
    return {
        "name": name,
        "title": raw["title"],
        "title_lv": raw.get("title_lv", ""),
        "domain": raw.get("domain", "management and human resources"),
        "institution": raw.get("institution", ""),
        "institution_lv": raw.get("institution_lv", ""),
        "sections": sections_list,
        "section_meta": section_meta,
        "chapter_headings": chapter_headings,
        "features": features,
        "paper_dir": paper_dir,
        "data_dir": paper_dir / "data",
    }


def load_active_paper() -> dict | None:
    name = get_active_paper_name()
    if name is None:
        return None
    return _parse_paper(name, load_paper_yaml(name))


def activate_paper(name: str) -> None:
    if not (PAPERS_DIR / name / "paper.yaml").exists():
        raise ValueError(f"Paper '{name}' not found in {PAPERS_DIR}")
    ACTIVE_PAPER_FILE.write_text(name, encoding="utf-8")


def _write_template_yaml(path: Path, title: str) -> None:
    safe_title = title.replace('"', '\\"')
    content = (
        f'title: "{safe_title}"\n'
        'institution: ""\n'
        'institution_lv: ""\n\n'
        "sections:\n"
        "  - id: introduction\n"
        '    title: "Introduction"\n'
        '    heading: "INTRODUCTION"\n'
        "    target_words: [500, 800]\n"
        "    kind: introduction\n\n"
        "  - id: chapter_1\n"
        '    title: "Chapter 1"\n'
        '    heading: "CHAPTER 1"\n'
        "    target_words: [800, 1200]\n"
        "    kind: subchapter\n"
        "    chapter: 1\n\n"
        "  - id: chapter_2\n"
        '    title: "Chapter 2"\n'
        '    heading: "CHAPTER 2"\n'
        "    target_words: [800, 1200]\n"
        "    kind: subchapter\n"
        "    chapter: 2\n\n"
        "  - id: conclusions\n"
        '    title: "Conclusions"\n'
        '    heading: "CONCLUSIONS"\n'
        "    target_words: [400, 600]\n"
        "    kind: conclusions\n\n"
        "chapter_headings:\n"
        '  1: "FIRST CHAPTER TITLE"\n'
        '  2: "SECOND CHAPTER TITLE"\n\n'
        "features:\n"
        "  bibliography: true\n"
        "  appendices: false\n"
    )
    path.write_text(content, encoding="utf-8")


def create_paper(name: str, title: str) -> None:
    paper_dir = PAPERS_DIR / name
    if paper_dir.exists():
        raise ValueError(f"Paper '{name}' already exists")
    paper_dir.mkdir(parents=True)
    data_dir = paper_dir / "data"
    (data_dir / "chapters").mkdir(parents=True)
    (data_dir / "appendices").mkdir(parents=True)
    (data_dir / "sources.json").write_text("[]", encoding="utf-8")
    _write_template_yaml(paper_dir / "paper.yaml", title)


def list_papers() -> list[str]:
    if not PAPERS_DIR.exists():
        return []
    return sorted(
        p.name for p in PAPERS_DIR.iterdir()
        if p.is_dir() and (p / "paper.yaml").exists()
    )
