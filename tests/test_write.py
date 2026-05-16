import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from cli import cli
from commands.evaluate import EvalResult


_DRAFT = (
    "This is an academic draft about management. {{cite:src_001:p.12}} "
    "Technology transforms organisational processes significantly. "
    "In conclusion, adoption offers substantial benefits."
)
_PASS_RESULT = EvalResult(passed=True, failures=[], word_count=750)
_FAIL_RESULT = EvalResult(
    passed=False,
    failures=[{"criterion": "tone", "detail": "Uses first person"}],
    word_count=200,
)


def test_write_saves_section_file(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    save_sources(sample_sources)
    runner = CliRunner()
    with patch("commands.write._generate_draft", return_value=_DRAFT), \
         patch("commands.write.evaluate", return_value=_PASS_RESULT):
        result = runner.invoke(cli, ["write", "--section", "chapter_1_1"])
    assert result.exit_code == 0
    assert (tmp_data_dir / "chapters" / "chapter_1_1.md").exists()


def test_write_marks_section_as_drafted(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    from core.state_manager import load_state
    save_sources(sample_sources)
    runner = CliRunner()
    with patch("commands.write._generate_draft", return_value=_DRAFT), \
         patch("commands.write.evaluate", return_value=_PASS_RESULT):
        runner.invoke(cli, ["write", "--section", "chapter_1_1"])
    assert load_state()["chapter_1_1"] == "drafted"


def test_write_retries_on_eval_failure(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    save_sources(sample_sources)
    runner = CliRunner()
    call_count = {"n": 0}
    def side_effect(*a, **kw):
        call_count["n"] += 1
        return _PASS_RESULT if call_count["n"] > 1 else _FAIL_RESULT

    with patch("commands.write._generate_draft", return_value=_DRAFT), \
         patch("commands.write.evaluate", side_effect=side_effect):
        result = runner.invoke(cli, ["write", "--section", "chapter_1_1"])
    assert call_count["n"] >= 2


def test_write_rejects_unknown_section(tmp_data_dir):
    runner = CliRunner()
    result = runner.invoke(cli, ["write", "--section", "nonexistent"])
    assert result.exit_code != 0 or "Unknown section" in result.output


def test_write_warns_after_max_retries(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    save_sources(sample_sources)
    runner = CliRunner()
    with patch("commands.write._generate_draft", return_value=_DRAFT), \
         patch("commands.write.evaluate", return_value=_FAIL_RESULT):
        result = runner.invoke(cli, ["write", "--section", "chapter_1_1"])
    assert result.exit_code == 0
    assert "manual review recommended" in result.output
    assert (tmp_data_dir / "chapters" / "chapter_1_1.md").exists()
