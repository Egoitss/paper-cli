import pytest
from unittest.mock import patch
from click.testing import CliRunner
from cli import cli


def test_run_improve_section_calls_targeted_and_master_passes(tmp_data_dir):
    import config
    (config.CHAPTERS_DIR / "chapter_1_1.md").write_text("Original text.", encoding="utf-8")

    call_log = []

    def fake_call(system, user, mode):
        call_log.append(mode)
        return "Improved text."

    with patch("commands.improve.call", side_effect=fake_call):
        with patch("commands.improve.mark_drafted"):
            from commands.improve import run_improve_section
            run_improve_section(
                "chapter_1_1",
                targeted=True, only=None,
                master=True,
                humanize=False, style=None,
                condense=False,
            )

    assert len(call_log) == 2  # one targeted pass, one master pass
    assert (config.CHAPTERS_DIR / "chapter_1_1.md").read_text(encoding="utf-8") == "Improved text."


def test_run_improve_section_skips_absent_section(tmp_data_dir):
    from commands.improve import run_improve_section
    with pytest.raises(SystemExit) as exc_info:
        run_improve_section(
            "chapter_1_1",
            targeted=True, only=None,
            master=True,
            humanize=False, style=None,
            condense=False,
        )
    assert exc_info.value.code == 1


def test_improve_all_skips_missing_sections(tmp_data_dir):
    import config
    (config.CHAPTERS_DIR / "chapter_1_1.md").write_text("Text.", encoding="utf-8")

    improved = []

    def fake_run(section, **kwargs):
        improved.append(section)

    with patch("commands.improve_all.run_improve_section", side_effect=fake_run):
        with patch("commands.improve_all.run_summary"):
            runner = CliRunner()
            result = runner.invoke(cli, ["improve-all", "--no-summary"])

    assert "chapter_1_1" in improved
    assert "chapter_4_2" not in improved  # no .md file for chapter_4_2
    assert result.exit_code == 0


def test_improve_all_regenerates_summary_by_default(tmp_data_dir):
    import config
    (config.CHAPTERS_DIR / "chapter_1_1.md").write_text("Text.", encoding="utf-8")

    with patch("commands.improve_all.run_improve_section"):
        with patch("commands.improve_all.run_summary") as mock_summary:
            runner = CliRunner()
            result = runner.invoke(cli, ["improve-all"])

    mock_summary.assert_called_once()
    assert result.exit_code == 0


def test_improve_all_no_summary_flag_skips_regen(tmp_data_dir):
    import config
    (config.CHAPTERS_DIR / "chapter_1_1.md").write_text("Text.", encoding="utf-8")

    with patch("commands.improve_all.run_improve_section"):
        with patch("commands.improve_all.run_summary") as mock_summary:
            runner = CliRunner()
            result = runner.invoke(cli, ["improve-all", "--no-summary"])

    mock_summary.assert_not_called()
    assert result.exit_code == 0
