"""
Word footnote support for python-docx via direct XML manipulation.

Creates a footnotes.xml part, registers it with the document, and provides
an API to insert footnote references into paragraphs.

Footnote format per Juridical College rules:
  - 10pt Times New Roman, single spacing, left aligned
  - Separated from body by a short line (Word handles this automatically)
  - Sequential numbering throughout the document
  - "Turpat" when the immediately preceding footnote cited the same source
"""
from __future__ import annotations
import re
from lxml import etree
from docx.opc.part import XmlPart
from docx.opc.packuri import PackURI

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_XML = "http://www.w3.org/XML/1998/namespace"
_FOOTNOTES_CT = (
    "application/vnd.openxmlformats-officedocument"
    ".wordprocessingml.footnotes+xml"
)
_FOOTNOTES_REL = (
    "http://schemas.openxmlformats.org/officeDocument"
    "/2006/relationships/footnotes"
)

def _w(tag: str) -> str:
    return f"{{{_W}}}{tag}"


# ── Page-reference conversion ─────────────────────────────────────────────────

_ART_SIMPLE   = re.compile(r"Art\.?\s*(\d+)$", re.I)
_ART_1        = re.compile(r"Art\.?\s*(\d+)[.(](\d+)\)?$", re.I)
_ART_2        = re.compile(r"Art\.?\s*(\d+)[.(]?(\d+)[.)]?\(([a-h])\)$", re.I)
_PARA         = re.compile(r"para\.?\s*(\d+)$", re.I)
_PAGE         = re.compile(r"p\.(\d+)$")
_RECITAL      = re.compile(r"recital\s*(\d+)$", re.I)


def format_page_ref_lv(ref: str) -> str:
    """Convert English citation ref to Latvian academic notation."""
    ref = ref.strip()
    if not ref:
        return ""
    if m := _ART_2.match(ref):
        return f"{m.group(1)}. panta {m.group(2)}. punkta {m.group(3)}) apakšpunkts"
    if m := _ART_1.match(ref):
        return f"{m.group(1)}. panta {m.group(2)}. punkts"
    if m := _ART_SIMPLE.match(ref):
        return f"{m.group(1)}. pants"
    if m := _PARA.match(ref):
        return f"{m.group(1)}. punkts"
    if m := _PAGE.match(ref):
        return f"{m.group(1)}. lpp."
    if m := _RECITAL.match(ref):
        return f"{m.group(1)}. apsvērums"
    lref = ref.lower()
    if lref == "preamble":
        return "Preambula"
    if lref == "summary":
        return "Kopsavilkums"
    return ref


# ── Source short titles for footnotes ────────────────────────────────────────

_SHORT_TITLES: dict[str, str] = {
    "src_001": "Regula (ES) 2016/679",
    "src_002": "EDAK Pamatnostādnes 01/2022",
    "src_003": "EST spriedums lietā C-487/21",
    "src_004": "EST spriedums lietā C-154/21",
    "src_005": "Vispārīgā datu aizsardzības regula (VDAR). EUR-Lex",
}


def build_footnote_text(src_id: str, page_ref: str, turpat: bool) -> str:
    page_lv = format_page_ref_lv(page_ref)
    if turpat:
        return f"Turpat, {page_lv}." if page_lv else "Turpat."
    short = _SHORT_TITLES.get(src_id, src_id)
    return f"{short}, {page_lv}." if page_lv else f"{short}."


# ── FootnoteManager ───────────────────────────────────────────────────────────

class FootnoteManager:
    """
    Creates and manages Word footnotes for a python-docx Document.

    Usage:
        fm = FootnoteManager(doc)
        fm.add(paragraph._p, "src_001", "Art.15")
    """

    def __init__(self, doc) -> None:
        self._doc = doc
        self._next_id = 1
        self._prev_src_id: str | None = None
        self._fn_root = self._build_root()
        self._register()

    # ── Initialisation ──────────────────────────────────────────────────────

    def _build_root(self):
        nsmap = {"w": _W}
        root = etree.Element(_w("footnotes"), nsmap=nsmap)
        for fn_type, fn_id, child_tag in (
            ("separator", "-1", "separator"),
            ("continuationSeparator", "0", "continuationSeparator"),
        ):
            fn = etree.SubElement(root, _w("footnote"))
            fn.set(_w("type"), fn_type)
            fn.set(_w("id"), fn_id)
            p = etree.SubElement(fn, _w("p"))
            r = etree.SubElement(p, _w("r"))
            etree.SubElement(r, _w(child_tag))
        return root

    def _register(self) -> None:
        part = XmlPart(
            PackURI("/word/footnotes.xml"),
            _FOOTNOTES_CT,
            self._fn_root,
            self._doc.part.package,
        )
        self._doc.part.relate_to(part, _FOOTNOTES_REL)

    # ── Public API ──────────────────────────────────────────────────────────

    def add(self, para_el, src_id: str, page_ref: str, fn_text: str | None = None) -> None:
        """Insert a footnote reference into *para_el* and register the footnote.

        If *fn_text* is provided it is used directly; otherwise the text is built
        from *src_id* / *page_ref* using the module-level _SHORT_TITLES lookup.
        """
        fn_id = self._next_id
        self._next_id += 1

        if fn_text is None:
            turpat = (self._prev_src_id == src_id)
            fn_text = build_footnote_text(src_id, page_ref, turpat)
        self._prev_src_id = src_id

        self._add_fn_xml(fn_id, fn_text)
        self._add_ref_xml(para_el, fn_id)

    # ── XML helpers ─────────────────────────────────────────────────────────

    def _add_fn_xml(self, fn_id: int, text: str) -> None:
        fn = etree.SubElement(self._fn_root, _w("footnote"))
        fn.set(_w("type"), "normal")
        fn.set(_w("id"), str(fn_id))

        p = etree.SubElement(fn, _w("p"))

        pPr = etree.SubElement(p, _w("pPr"))
        jc = etree.SubElement(pPr, _w("jc"))
        jc.set(_w("val"), "left")
        spacing = etree.SubElement(pPr, _w("spacing"))
        spacing.set(_w("line"), "240")        # single (240 twips = 1 line)
        spacing.set(_w("lineRule"), "auto")
        spacing.set(_w("before"), "0")
        spacing.set(_w("after"), "0")

        # Auto footnote number mark
        r_mark = etree.SubElement(p, _w("r"))
        rPr_mark = etree.SubElement(r_mark, _w("rPr"))
        _fn_rpr_font(rPr_mark, superscript=True)
        etree.SubElement(r_mark, _w("footnoteRef"))

        # Footnote text
        r_text = etree.SubElement(p, _w("r"))
        rPr_text = etree.SubElement(r_text, _w("rPr"))
        _fn_rpr_font(rPr_text, superscript=False)
        t = etree.SubElement(r_text, _w("t"))
        t.set(f"{{{_XML}}}space", "preserve")
        t.text = " " + text

    @staticmethod
    def _add_ref_xml(para_el, fn_id: int) -> None:
        r = etree.SubElement(para_el, _w("r"))
        rPr = etree.SubElement(r, _w("rPr"))
        vertAlign = etree.SubElement(rPr, _w("vertAlign"))
        vertAlign.set(_w("val"), "superscript")
        sz = etree.SubElement(rPr, _w("sz"))
        sz.set(_w("val"), "20")
        szCs = etree.SubElement(rPr, _w("szCs"))
        szCs.set(_w("val"), "20")
        ref = etree.SubElement(r, _w("footnoteReference"))
        ref.set(_w("id"), str(fn_id))


def _fn_rpr_font(rPr_el, superscript: bool = False) -> None:
    fonts = etree.SubElement(rPr_el, _w("rFonts"))
    fonts.set(_w("ascii"), "Times New Roman")
    fonts.set(_w("hAnsi"), "Times New Roman")
    sz = etree.SubElement(rPr_el, _w("sz"))
    sz.set(_w("val"), "20")   # 10pt = 20 half-points
    szCs = etree.SubElement(rPr_el, _w("szCs"))
    szCs.set(_w("val"), "20")
    if superscript:
        va = etree.SubElement(rPr_el, _w("vertAlign"))
        va.set(_w("val"), "superscript")
