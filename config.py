import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── API settings ──────────────────────────────────────────────────────────────
API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
MODEL: str = "claude-sonnet-4-6"

# Per-command temperatures: lower = more deterministic (evaluate/cite), higher = more creative (write)
TEMPERATURE: dict[str, float] = {
    "research": 0.3,
    "write": 0.6,
    "evaluate": 0.1,
    "cite": 0.2,
}

BASE_DIR = Path(__file__).parent

# ── Paper-specific config ─────────────────────────────────────────────────────
# Loaded dynamically from the active paper's paper.yaml at import time.
# Falls back to hardcoded values when no paper is active (fresh clone, test env).

try:
    from core import paper_manager as _pm
    _paper = _pm.load_active_paper()
except Exception:
    _paper = None

if _paper:
    PAPER_TITLE: str = _paper["title"]
    PAPER_TITLE_LV: str = _paper["title_lv"]
    PAPER_DOMAIN: str = _paper["domain"]
    INSTITUTION: str = _paper["institution"]
    INSTITUTION_LV: str = _paper["institution_lv"]
    SECTIONS: list[str] = _paper["sections"]
    SECTION_META: dict[str, dict] = _paper["section_meta"]
    CHAPTER_HEADINGS: dict[int, str] = _paper["chapter_headings"]
    FEATURES: dict[str, bool] = _paper["features"]
    PAPER_DIR: Path = _paper["paper_dir"]
    DATA_DIR: Path = _paper["data_dir"]
else:
    # Fallback: hardcoded values used when no paper is active (fresh clone, test env)
    PAPER_DOMAIN: str = "management and human resources"
    PAPER_TITLE_LV: str = ""
    INSTITUTION: str = ""
    INSTITUTION_LV: str = ""
    PAPER_TITLE = (
        "The Use of Artificial Intelligence in the Recruitment Process "
        "and Human Resource Management"
    )
    SECTIONS: list[str] = [
        "introduction",
        "chapter_1_1", "chapter_1_2",
        "chapter_2_1", "chapter_2_2",
        "chapter_3_1", "chapter_3_2",
        "chapter_4_1", "chapter_4_2",
        "conclusions",
    ]
    SECTION_META: dict[str, dict] = {
        "introduction": {
            "title": "Introduction", "heading": "INTRODUCTION",
            "target_words": (800, 1000), "kind": "introduction",
        },
        "chapter_1_1": {
            "title": "1.1 AI in Modern HR: Overview and Evolution",
            "heading": "1.1 AI in Modern HR: Overview and Evolution",
            "target_words": (600, 900), "kind": "subchapter", "chapter": 1,
        },
        "chapter_1_2": {
            "title": "1.2 Key AI Technologies Used in HR",
            "heading": "1.2 Key AI Technologies Used in HR",
            "target_words": (600, 900), "kind": "subchapter", "chapter": 1,
        },
        "chapter_2_1": {
            "title": "2.1 AI in Talent Sourcing and Screening",
            "heading": "2.1 AI in Talent Sourcing and Screening",
            "target_words": (600, 900), "kind": "subchapter", "chapter": 2,
        },
        "chapter_2_2": {
            "title": "2.2 AI in Interviewing and Candidate Assessment",
            "heading": "2.2 AI in Interviewing and Candidate Assessment",
            "target_words": (600, 900), "kind": "subchapter", "chapter": 2,
        },
        "chapter_3_1": {
            "title": "3.1 Case Studies: AI Adoption in Recruitment Practice",
            "heading": "3.1 Case Studies: AI Adoption in Recruitment Practice",
            "target_words": (600, 900), "kind": "empirical", "chapter": 3,
        },
        "chapter_3_2": {
            "title": "3.2 AI in Performance Management and Retention",
            "heading": "3.2 AI in Performance Management and Retention",
            "target_words": (600, 900), "kind": "empirical", "chapter": 3,
        },
        "chapter_4_1": {
            "title": "4.1 Challenges, Bias and Ethical Considerations",
            "heading": "4.1 Challenges, Bias and Ethical Considerations",
            "target_words": (600, 900), "kind": "subchapter", "chapter": 4,
        },
        "chapter_4_2": {
            "title": "4.2 Legal Frameworks and Future Trends",
            "heading": "4.2 Legal Frameworks and Future Trends",
            "target_words": (600, 900), "kind": "subchapter", "chapter": 4,
        },
        "conclusions": {
            "title": "Conclusions and Proposals",
            "heading": "CONCLUSIONS AND PROPOSALS",
            "target_words": (800, 1000), "kind": "conclusions",
        },
    }
    CHAPTER_HEADINGS: dict[int, str] = {
        1: "AI IN HUMAN RESOURCE MANAGEMENT: CONCEPTS AND TECHNOLOGIES",
        2: "AI IN THE RECRUITMENT PROCESS",
        3: "EMPIRICAL ANALYSIS: AI ADOPTION IN HR PRACTICE",
        4: "CHALLENGES, ETHICS, LEGAL FRAMEWORKS AND FUTURE TRENDS",
    }
    FEATURES: dict[str, bool] = {"bibliography": True, "appendices": True}
    PAPER_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"

# ── Derived paths (same for all papers) ──────────────────────────────────────
SOURCES_FILE: Path = DATA_DIR / "sources.json"
STATE_FILE: Path = DATA_DIR / "project_state.md"
CHAPTERS_DIR: Path = DATA_DIR / "chapters"
APPENDICES_DIR: Path = DATA_DIR / "appendices"

# ── Source collection targets ─────────────────────────────────────────────────
# SOURCE_MINIMUMS enforced by check_distribution(); TOTAL_SOURCES_TARGET is advisory
SOURCE_MINIMUMS: dict[str, int] = {"scientific": 3, "legal": 2}
TOTAL_SOURCES_TARGET: int = 25
