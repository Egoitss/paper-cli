import pytest
import yaml
from click.testing import CliRunner
from cli import cli


def test_use_command_activates_paper(tmp_papers_dir):
    import core.paper_manager as pm
    # Create a paper to activate
    (tmp_papers_dir / "papers" / "my_paper").mkdir()
    (tmp_papers_dir / "papers" / "my_paper" / "paper.yaml").write_text(
        'title: "My Paper"\nsections: []\nfeatures:\n  bibliography: true\n  appendices: false\n',
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["use", "my_paper"])
    assert result.exit_code == 0, result.output
    assert pm.get_active_paper_name() == "my_paper"


def test_use_command_fails_for_nonexistent_paper(tmp_papers_dir):
    runner = CliRunner()
    result = runner.invoke(cli, ["use", "nonexistent"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_new_command_creates_paper_and_activates(tmp_papers_dir):
    import core.paper_manager as pm
    runner = CliRunner()
    result = runner.invoke(cli, ["new", "my_thesis", "--title", "My Thesis Title"])
    assert result.exit_code == 0, result.output
    paper_dir = tmp_papers_dir / "papers" / "my_thesis"
    assert paper_dir.exists()
    assert (paper_dir / "paper.yaml").exists()
    assert (paper_dir / "data" / "chapters").exists()
    assert (paper_dir / "data" / "sources.json").read_text(encoding="utf-8") == "[]"
    cfg = yaml.safe_load((paper_dir / "paper.yaml").read_text(encoding="utf-8"))
    assert cfg["title"] == "My Thesis Title"
    assert pm.get_active_paper_name() == "my_thesis"


def test_new_command_fails_if_paper_exists(tmp_papers_dir):
    runner = CliRunner()
    runner.invoke(cli, ["new", "dup", "--title", "First"])
    result = runner.invoke(cli, ["new", "dup", "--title", "Second"])
    assert result.exit_code != 0


def test_list_command_shows_all_papers(tmp_papers_dir):
    import core.paper_manager as pm
    pm.create_paper("paper_a", "Paper A")
    pm.create_paper("paper_b", "Paper B")
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0, result.output
    assert "paper_a" in result.output
    assert "paper_b" in result.output


def test_list_command_marks_active_paper(tmp_papers_dir):
    import core.paper_manager as pm
    pm.create_paper("paper_a", "Paper A")
    pm.create_paper("paper_b", "Paper B")
    pm.activate_paper("paper_a")
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    active_line = next(l for l in lines if "paper_a" in l)
    assert active_line.startswith("*")


def test_list_command_no_papers(tmp_papers_dir):
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "no papers" in result.output.lower() or "paper new" in result.output.lower()


def test_list_command_shows_unreadable_fallback_for_corrupt_yaml(tmp_papers_dir):
    papers = tmp_papers_dir / "papers"
    corrupt_dir = papers / "corrupt_paper"
    corrupt_dir.mkdir()
    (corrupt_dir / "paper.yaml").write_text(": invalid: yaml: [", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "corrupt_paper" in result.output
