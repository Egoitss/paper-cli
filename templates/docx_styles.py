from docx.shared import Pt, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH

STYLES: dict = {
    "page": {
        "width": Mm(210),
        "height": Mm(297),
        "margin_left": Mm(30),
        "margin_right": Mm(15),
        "margin_top": Mm(20),
        "margin_bottom": Mm(20),
    },
    "body": {
        "font": "Times New Roman",
        "size": Pt(12),
        "line_spacing": 1.5,
        "first_line_indent": Mm(15),
        "alignment": WD_ALIGN_PARAGRAPH.JUSTIFY,
    },
    "chapter_heading": {
        "font": "Times New Roman",
        "size": Pt(14),
        "bold": True,
        "all_caps": True,
        "alignment": WD_ALIGN_PARAGRAPH.LEFT,
        "space_before": Pt(0),
        "space_after": Pt(6),
        "page_break_before": True,
    },
    "subchapter_heading": {
        "font": "Times New Roman",
        "size": Pt(12),
        "small_caps": True,
        "bold": False,
        "alignment": WD_ALIGN_PARAGRAPH.LEFT,
        "space_before": Pt(6),
        "space_after": Pt(3),
    },
    "footnote": {
        "font": "Times New Roman",
        "size": Pt(10),
        "line_spacing": 1.0,
        "alignment": WD_ALIGN_PARAGRAPH.LEFT,
    },
    "page_number": {
        "position": "top_center",
    },
}
