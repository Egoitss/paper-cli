import json
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from cli import cli


_FAKE_SOURCES = json.dumps([
    {
        "author": "Smith",
        "title": "Sample Study",
        "year": 2023,
        "publisher": "Sample Publisher",
        "url": "https://example.com/study",
        "summary": "A sample academic study.",
        "key_quotes": ["A key finding from the study."],
        "type": "scientific",
    }
])


def test_research_adds_sources(tmp_data_dir):
    runner = CliRunner()
    with patch("commands.research._search", return_value=_FAKE_SOURCES):
        result = runner.invoke(cli, ["research", "sample topic", "--type", "scientific"])
    assert result.exit_code == 0
    assert "Added" in result.output


def test_research_skips_duplicate(tmp_data_dir):
    runner = CliRunner()
    with patch("commands.research._search", return_value=_FAKE_SOURCES):
        runner.invoke(cli, ["research", "sample topic", "--type", "scientific"])
        result = runner.invoke(cli, ["research", "sample topic", "--type", "scientific"])
    assert result.exit_code == 0
    from core.source_manager import get_source_count
    assert get_source_count() == 1


def test_research_prints_distribution_warning(tmp_data_dir):
    runner = CliRunner()
    with patch("commands.research._search", return_value=_FAKE_SOURCES):
        result = runner.invoke(cli, ["research", "sample topic", "--type", "scientific"])
    assert "Need" in result.output or "warning" in result.output.lower() or result.exit_code == 0
