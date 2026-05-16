import json
import pytest
from click.testing import CliRunner
from cli import cli


def _setup(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    from core.state_manager import mark_approved
    save_sources(sample_sources)
    (tmp_data_dir / "chapters" / "introduction.md").write_text(
        "This is the introduction.", encoding="utf-8"
    )
    mark_approved("introduction")
    (tmp_data_dir / "citations.json").write_text(
        json.dumps({"footnotes": [], "bibliography": [], "abbreviations": []}),
        encoding="utf-8",
    )


def test_build_creates_docx(tmp_data_dir, sample_sources):
    _setup(tmp_data_dir, sample_sources)
    out_file = tmp_data_dir / "submission_draft.docx"
    runner = CliRunner()
    result = runner.invoke(cli, ["build", "--output", str(out_file)])
    assert result.exit_code == 0
    assert out_file.exists()


def test_build_fails_gracefully_without_citations(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    save_sources(sample_sources)
    runner = CliRunner()
    result = runner.invoke(cli, ["build"])
    assert "citations.json" in result.output or result.exit_code != 0
