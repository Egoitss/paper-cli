import json
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from cli import cli


# --- strip_cite_markers ---

def test_strip_cite_markers_removes_all_markers():
    from commands.summary import strip_cite_markers
    text = "AI is growing {{cite:src_026:p.3}}. It affects HR {{cite:src_001:p.15}}."
    assert strip_cite_markers(text) == "AI is growing . It affects HR ."


def test_strip_cite_markers_leaves_plain_text():
    from commands.summary import strip_cite_markers
    assert strip_cite_markers("No markers here.") == "No markers here."


# --- format_bib_entry ---

def test_format_bib_entry_full_source():
    from commands.summary import format_bib_entry
    src = {
        "author": "Tambe, Cappelli",
        "title": "AI in HR",
        "publisher": "California Management Review",
        "year": 2019,
        "url": "https://example.com",
    }
    result = format_bib_entry(src)
    assert "Tambe, Cappelli." in result
    assert "AI in HR." in result
    assert "2019." in result
    assert "https://example.com" in result


def test_format_bib_entry_missing_author():
    from commands.summary import format_bib_entry
    src = {"author": "", "title": "GDPR", "year": 2016, "publisher": "EU", "url": "https://gdpr.eu"}
    result = format_bib_entry(src)
    assert result.startswith("GDPR.")


# --- get_intro_sources ---

def test_get_intro_sources_returns_cited_sources(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    import config
    save_sources(sample_sources)
    intro = "AI use is growing {{cite:src_001:p.3}}. GDPR applies {{cite:src_002:p.1}}."
    (config.CHAPTERS_DIR / "introduction.md").write_text(intro, encoding="utf-8")

    from commands.summary import get_intro_sources
    result = get_intro_sources()
    assert len(result) == 2
    assert result[0]["id"] == "src_001"
    assert result[1]["id"] == "src_002"


def test_get_intro_sources_deduplicates(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    import config
    save_sources(sample_sources)
    intro = "First {{cite:src_001:p.3}}. Second {{cite:src_001:p.5}}."
    (config.CHAPTERS_DIR / "introduction.md").write_text(intro, encoding="utf-8")

    from commands.summary import get_intro_sources
    result = get_intro_sources()
    assert len(result) == 1


def test_get_intro_sources_preserves_order(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    import config
    save_sources(sample_sources)
    intro = "B {{cite:src_002:p.1}}. A {{cite:src_001:p.1}}."
    (config.CHAPTERS_DIR / "introduction.md").write_text(intro, encoding="utf-8")

    from commands.summary import get_intro_sources
    result = get_intro_sources()
    assert result[0]["id"] == "src_002"
    assert result[1]["id"] == "src_001"


# --- generate_summaries ---

def test_generate_summaries_parses_json_response(tmp_data_dir):
    import config
    (config.CHAPTERS_DIR / "chapter_1_1.md").write_text(
        "This chapter examines AI history {{cite:src_001:p.1}}.", encoding="utf-8"
    )
    api_response = json.dumps({"chapter_1_1": "AI evolved through several phases."})

    with patch("commands.summary.call", return_value=api_response):
        from commands.summary import generate_summaries
        result = generate_summaries(["chapter_1_1"])

    assert result == {"chapter_1_1": "AI evolved through several phases."}


def test_generate_summaries_handles_markdown_wrapped_json(tmp_data_dir):
    import config
    (config.CHAPTERS_DIR / "chapter_1_1.md").write_text("Chapter text.", encoding="utf-8")
    api_response = '```json\n{"chapter_1_1": "Short summary."}\n```'

    with patch("commands.summary.call", return_value=api_response):
        from commands.summary import generate_summaries
        result = generate_summaries(["chapter_1_1"])

    assert result["chapter_1_1"] == "Short summary."


# --- build_summary_docx ---

def test_build_summary_docx_contains_intro_text(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    import config
    save_sources(sample_sources)
    (config.CHAPTERS_DIR / "introduction.md").write_text(
        "AI is transforming HR. {{cite:src_001:p.1}}", encoding="utf-8"
    )

    from commands.summary import build_summary_docx
    doc = build_summary_docx(summaries={}, sources=[])
    all_text = " ".join(p.text for p in doc.paragraphs)
    assert "AI is transforming HR." in all_text


def test_build_summary_docx_chapter_headings_present(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    import config
    save_sources(sample_sources)
    (config.CHAPTERS_DIR / "introduction.md").write_text("Intro text.", encoding="utf-8")

    from commands.summary import build_summary_docx
    doc = build_summary_docx(
        summaries={"chapter_1_1": "AI evolved."},
        sources=[],
    )
    all_text = " ".join(p.text for p in doc.paragraphs)
    assert "1.1 AI IN MODERN HR" in all_text.upper()
    assert "AI evolved." in all_text


def test_build_summary_docx_name_only_for_undrafted(tmp_data_dir):
    import config
    (config.CHAPTERS_DIR / "introduction.md").write_text("Intro.", encoding="utf-8")

    from commands.summary import build_summary_docx
    doc = build_summary_docx(summaries={}, sources=[])
    all_text = " ".join(p.text for p in doc.paragraphs)
    assert "4.2" in all_text
    assert "CONCLUSIONS" in all_text.upper()


def test_build_summary_docx_literature_section(tmp_data_dir):
    import config
    (config.CHAPTERS_DIR / "introduction.md").write_text("Intro.", encoding="utf-8")
    src = {"author": "Tambe", "title": "AI in HR", "year": 2019, "publisher": "CMR", "url": "https://x.com"}

    from commands.summary import build_summary_docx
    doc = build_summary_docx(summaries={}, sources=[src])
    all_text = " ".join(p.text for p in doc.paragraphs)
    assert "LITERATURE" in all_text.upper()
    assert "Tambe." in all_text


# --- CLI integration ---

def test_summary_cli_creates_docx(tmp_data_dir, sample_sources, tmp_path):
    from core.source_manager import save_sources
    import config
    save_sources(sample_sources)
    (config.CHAPTERS_DIR / "introduction.md").write_text(
        "AI is growing {{cite:src_001:p.3}}.", encoding="utf-8"
    )
    for sec in ["chapter_1_1", "chapter_1_2", "chapter_2_1", "chapter_2_2",
                "chapter_3_1", "chapter_3_2", "chapter_4_1"]:
        (config.CHAPTERS_DIR / f"{sec}.md").write_text(f"Content of {sec}.", encoding="utf-8")

    output = str(tmp_path / "out.docx")
    summaries = {s: f"Summary of {s}." for s in
                 ["chapter_1_1", "chapter_1_2", "chapter_2_1", "chapter_2_2",
                  "chapter_3_1", "chapter_3_2", "chapter_4_1"]}

    runner = CliRunner()
    with patch("commands.summary.call", return_value=json.dumps(summaries)):
        result = runner.invoke(cli, ["summary", "--output", output])

    assert result.exit_code == 0, result.output
    from pathlib import Path
    assert Path(output).exists()


def test_generate_summaries_system_prompt_is_analytical(tmp_data_dir):
    import config
    (config.CHAPTERS_DIR / "chapter_1_1.md").write_text("Chapter text.", encoding="utf-8")
    captured = {}

    def fake_call(system, user, mode):
        captured["system"] = system
        captured["user"] = user
        return json.dumps({"chapter_1_1": "AI shaped HR through three technological waves."})

    with patch("commands.summary.call", side_effect=fake_call):
        from commands.summary import generate_summaries
        generate_summaries(["chapter_1_1"])

    assert "formal academic prose" not in captured["system"].lower()
    assert any(kw in captured["system"].lower() for kw in ("analytical", "argument", "significance"))


def test_generate_summaries_user_prompt_says_synthesise(tmp_data_dir):
    import config
    (config.CHAPTERS_DIR / "chapter_1_1.md").write_text("Chapter text.", encoding="utf-8")
    captured = {}

    def fake_call(system, user, mode):
        captured["user"] = user
        return json.dumps({"chapter_1_1": "AI shaped HR."})

    with patch("commands.summary.call", side_effect=fake_call):
        from commands.summary import generate_summaries
        generate_summaries(["chapter_1_1"])

    assert any(kw in captured["user"].lower() for kw in ("synthesise", "synthesize", "significance", "argument"))
    assert "formal academic prose" not in captured["user"].lower()
