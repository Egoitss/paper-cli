import os
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-placeholder")

import pytest
from pathlib import Path


@pytest.fixture
def tmp_data_dir(tmp_path: Path, monkeypatch) -> Path:
    import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "PAPER_DIR", tmp_path)
    monkeypatch.setattr(config, "SOURCES_FILE", tmp_path / "sources.json")
    monkeypatch.setattr(config, "STATE_FILE", tmp_path / "project_state.md")
    monkeypatch.setattr(config, "CHAPTERS_DIR", tmp_path / "chapters")
    monkeypatch.setattr(config, "APPENDICES_DIR", tmp_path / "appendices")
    (tmp_path / "chapters").mkdir()
    (tmp_path / "appendices").mkdir()
    (tmp_path / "sources.json").write_text("[]", encoding="utf-8")
    return tmp_path


@pytest.fixture
def tmp_papers_dir(tmp_path: Path, monkeypatch) -> Path:
    """Isolates paper_manager from the real filesystem for management command tests."""
    import core.paper_manager as pm
    papers = tmp_path / "papers"
    papers.mkdir()
    active_file = tmp_path / ".active_paper"
    monkeypatch.setattr(pm, "PAPERS_DIR", papers)
    monkeypatch.setattr(pm, "ACTIVE_PAPER_FILE", active_file)
    return tmp_path


@pytest.fixture
def sample_sources() -> list[dict]:
    return [
        {
            "id": "src_001",
            "author": "Brynjolfsson",
            "title": "The Second Machine Age",
            "year": 2014,
            "publisher": "W. W. Norton",
            "url": "https://example.com/1",
            "summary": "An examination of AI's economic impact.",
            "key_quotes": ["AI is transforming work."],
            "type": "scientific",
        },
        {
            "id": "src_002",
            "author": "",
            "title": "General Data Protection Regulation",
            "year": 2016,
            "publisher": "European Union",
            "url": "https://gdpr.eu",
            "summary": "EU data protection regulation.",
            "key_quotes": [],
            "type": "legal",
        },
    ]
