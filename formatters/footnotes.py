from __future__ import annotations
import re
from core.markers import CITE_RE as _CITE_RE

# Matches standalone ALL-CAPS tokens 2+ chars long (abbreviations like AI, HR, GDPR)
_ABBREV_RE = re.compile(r"\b([A-Z]{2,})\b")

# Maps digit characters to their Unicode superscript equivalents
_SUPERSCRIPTS = {
    "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵",
    "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "0": "⁰",
}


def _to_superscript(n: int) -> str:
    return "".join(_SUPERSCRIPTS.get(c, c) for c in str(n))


def extract_citations(text: str) -> list[dict]:
    # Returns one dict per {{cite:...}} marker found in the text
    return [
        {"source_id": m.group(1), "page": m.group(2) or "", "marker": m.group(0)}
        for m in _CITE_RE.finditer(text)
    ]


def assign_footnote_numbers(sections: dict[str, str]) -> dict[str, list[dict]]:
    # Iterates sections in the order provided (caller must pass them in config.SECTIONS order)
    # so footnote numbers are deterministic across the whole document
    counter = 1
    result: dict[str, list[dict]] = {}
    for section_id, text in sections.items():
        citations = extract_citations(text)
        numbered = []
        for c in citations:
            numbered.append({**c, "number": counter})
            counter += 1
        result[section_id] = numbered
    return result


def replace_markers(text: str, mapping: dict[str, int]) -> str:
    # Two-pass replacement: first consume the space before the marker (standard typography),
    # then fall back to replacing the bare marker (handles markers after punctuation)
    for marker, number in mapping.items():
        sup = _to_superscript(number)
        text = text.replace(" " + marker, sup)
        text = text.replace(marker, sup)
    return text


def extract_abbreviations(text: str) -> list[str]:
    """Find all ALL-CAPS tokens ≥2 chars; return sorted unique list."""
    found = set(_ABBREV_RE.findall(text))
    return sorted(found)
