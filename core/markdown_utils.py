from __future__ import annotations
import re

HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"\*(.+?)\*")
HR_RE = re.compile(r"^-{3,}$", re.MULTILINE)


def strip_markdown(text: str) -> str:
    """Remove bold/italic markers and collapse extra spaces."""
    text = BOLD_RE.sub(r"\1", text)
    text = ITALIC_RE.sub(r"\1", text)
    return re.sub(r"  +", " ", text).strip()
