from __future__ import annotations
import re


def apply_terminology(text: str, terms: dict[str, str]) -> str:
    """Replace whole-word English terms with their mapped equivalents."""
    for src, dst in terms.items():
        text = re.sub(r"\b" + re.escape(src) + r"\b", dst, text)
    return text
