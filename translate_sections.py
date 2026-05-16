"""
Translate condensed English chapter files to Latvian using Google Translate.
Preserves {{cite:...}} markers and Markdown headings.
Post-processes with terminology corrections.
"""
from __future__ import annotations
import re
import time
from pathlib import Path
from deep_translator import GoogleTranslator
from core.markers import CITE_RE as _CITE_RE
from core.markdown_utils import HEADING_RE as _HEADING_RE
from core.text_utils import apply_terminology

CHAPTERS_DIR = Path("papers/report_1/data/chapters")
SECTIONS = ["introduction", "part_1", "part_2", "conclusions"]

TERMINOLOGY = {
    "Vispārīgā datu aizsardzības regula": "Vispārīgā datu aizsardzības regula",
    "CJEU": "EST",
    "Court of Justice": "Eiropas Savienības Tiesa",
    "Court of Justice of the European Union": "Eiropas Savienības Tiesa",
    "EDPB": "EDAK",
    "European Data Protection Board": "Eiropas Datu aizsardzības kolēģija",
    "GDPR": "VDAR",
    "General Data Protection Regulation": "Vispārīgā datu aizsardzības regula",
    "Article 15": "15. pants",
    "Article 12": "12. pants",
    "Article 23": "23. pants",
    "Article 15(1)": "15. panta 1. punkts",
    "Article 15(3)": "15. panta 3. punkts",
    "Article 15(1)(c)": "15. panta 1. punkta c) apakšpunkts",
    "Regulation (EU) 2016/679": "Regula (ES) 2016/679",
    "data subject": "datu subjekts",
    "data subjects": "datu subjekti",
    "controller": "pārzinis",
    "controllers": "pārziņi",
    "personal data": "personas dati",
    "right of access": "piekļuves tiesības",
    "right to access": "tiesības piekļūt",
    "supervisory authority": "uzraudzības iestāde",
    "supervisory authorities": "uzraudzības iestādes",
    "Turpat": "Turpat",
}


def _extract_placeholders(text: str) -> tuple[str, dict[str, str]]:
    """Replace {{cite:...}} with CCCITE0CCC placeholders."""
    placeholders: dict[str, str] = {}
    counter = [0]

    def replace(m: re.Match) -> str:
        key = f"CCCITE{counter[0]}CCC"
        placeholders[key] = m.group(0)
        counter[0] += 1
        return key

    return _CITE_RE.sub(replace, text), placeholders


def _restore_placeholders(text: str, placeholders: dict[str, str]) -> str:
    for key, val in placeholders.items():
        text = text.replace(key, val)
    return text


def translate_paragraph(translator: GoogleTranslator, para: str) -> str:
    para_with_ph, ph = _extract_placeholders(para)
    # Split into chunks ≤4500 chars for Google Translate limit
    if len(para_with_ph) <= 4500:
        translated = translator.translate(para_with_ph)
    else:
        parts = []
        chunk = ""
        for sentence in re.split(r"(?<=[.!?])\s+", para_with_ph):
            if len(chunk) + len(sentence) + 1 > 4500:
                parts.append(translator.translate(chunk.strip()))
                chunk = sentence
            else:
                chunk = (chunk + " " + sentence).strip()
        if chunk:
            parts.append(translator.translate(chunk.strip()))
        translated = " ".join(parts)
    return _restore_placeholders(translated or para_with_ph, ph)


def translate_section(section_id: str) -> None:
    src_path = CHAPTERS_DIR / f"{section_id}.md"
    dst_path = CHAPTERS_DIR / f"{section_id}_lv.md"

    text = src_path.read_text(encoding="utf-8")
    translator = GoogleTranslator(source="en", target="lv")

    paragraphs = text.split("\n\n")
    translated_paragraphs: list[str] = []

    for i, para in enumerate(paragraphs):
        stripped = para.strip()
        if not stripped:
            translated_paragraphs.append("")
            continue

        # Preserve Markdown headings (only translate the heading text)
        if _HEADING_RE.match(stripped):
            m = _HEADING_RE.match(stripped)
            hashes = m.group(0)
            heading_text = stripped[m.end():]
            translated_heading = translator.translate(heading_text)
            translated_paragraphs.append(f"{hashes}{translated_heading}")
            time.sleep(0.3)
            continue

        translated = translate_paragraph(translator, stripped)
        translated_paragraphs.append(translated)
        time.sleep(0.3)
        print(f"  [{section_id}] para {i+1}/{len(paragraphs)} done")

    result = "\n\n".join(translated_paragraphs)
    result = apply_terminology(result, TERMINOLOGY)
    dst_path.write_text(result, encoding="utf-8")
    print(f"Saved: {dst_path} ({len(result.split())} words)")


if __name__ == "__main__":
    import sys
    sections = sys.argv[1:] if len(sys.argv) > 1 else SECTIONS
    for sec in sections:
        print(f"\nTranslating {sec}...")
        translate_section(sec)
    print("\nDone.")
