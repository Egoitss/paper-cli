import json
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from cli import cli


def _write_chapter(tmp_data_dir, filename, content):
    path = tmp_data_dir / "chapters" / filename
    path.write_text(content, encoding="utf-8")


def test_cite_creates_citations_json(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    from core.state_manager import mark_approved
    save_sources(sample_sources)
    _write_chapter(tmp_data_dir, "chapter_1_1.md",
                   "AI is useful {{cite:src_001:p.5}} in hiring.")
    mark_approved("chapter_1_1")

    runner = CliRunner()
    result = runner.invoke(cli, ["cite"])
    assert result.exit_code == 0
    citations_file = tmp_data_dir / "citations.json"
    assert citations_file.exists()


def test_cite_assigns_sequential_numbers(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    from core.state_manager import mark_approved
    save_sources(sample_sources)
    _write_chapter(tmp_data_dir, "chapter_1_1.md",
                   "First {{cite:src_001:p.1}}. Second {{cite:src_002:p.2}}.")
    _write_chapter(tmp_data_dir, "chapter_1_2.md",
                   "Third {{cite:src_001:p.3}}.")
    mark_approved("chapter_1_1")
    mark_approved("chapter_1_2")

    runner = CliRunner()
    runner.invoke(cli, ["cite"])
    data = json.loads((tmp_data_dir / "citations.json").read_text())
    numbers = [fn["number"] for fn in data["footnotes"]]
    assert numbers == [1, 2, 3]


def test_cite_bibliography_contains_all_sources(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    from core.state_manager import mark_approved
    save_sources(sample_sources)
    _write_chapter(tmp_data_dir, "introduction.md",
                   "See {{cite:src_001:p.1}} and {{cite:src_002:p.2}}.")
    mark_approved("introduction")

    runner = CliRunner()
    runner.invoke(cli, ["cite"])
    data = json.loads((tmp_data_dir / "citations.json").read_text())
    assert len(data["bibliography"]) == 2
