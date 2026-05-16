import pytest
from formatters.footnotes import (
    extract_citations,
    assign_footnote_numbers,
    replace_markers,
    extract_abbreviations,
)


def test_extract_citations_finds_markers():
    text = "AI is growing {{cite:src_001:p.12}} rapidly {{cite:src_002:p.45}}."
    citations = extract_citations(text)
    assert len(citations) == 2
    assert citations[0] == {"source_id": "src_001", "page": "p.12", "marker": "{{cite:src_001:p.12}}"}
    assert citations[1] == {"source_id": "src_002", "page": "p.45", "marker": "{{cite:src_002:p.45}}"}


def test_assign_footnote_numbers_sequential():
    sections = {
        "chapter_1_1": "Text {{cite:src_001:p.1}} more {{cite:src_002:p.2}}.",
        "chapter_1_2": "Next {{cite:src_003:p.3}} text.",
    }
    result = assign_footnote_numbers(sections)
    assert result["chapter_1_1"][0]["number"] == 1
    assert result["chapter_1_1"][1]["number"] == 2
    assert result["chapter_1_2"][0]["number"] == 3


def test_replace_markers_substitutes_numbers():
    text = "Text {{cite:src_001:p.12}} here."
    mapping = {"{{cite:src_001:p.12}}": 1}
    result = replace_markers(text, mapping)
    assert result == "Text¹ here."
    assert "{{cite:" not in result


def test_extract_abbreviations_finds_all_caps():
    text = "The AI system uses NLP and ML. The HRM department adopted RPA tools."
    abbrevs = extract_abbreviations(text)
    assert "AI" in abbrevs
    assert "NLP" in abbrevs
    assert "ML" in abbrevs
    assert "HRM" in abbrevs
    assert "RPA" in abbrevs


def test_extract_abbreviations_excludes_single_chars():
    text = "The A system uses I and O values."
    abbrevs = extract_abbreviations(text)
    assert "A" not in abbrevs
    assert "I" not in abbrevs


def test_extract_abbreviations_returns_sorted_unique():
    text = "AI uses NLP. AI and ML and NLP are common AI terms."
    abbrevs = extract_abbreviations(text)
    assert abbrevs == sorted(set(abbrevs))
    assert abbrevs.count("AI") == 1
