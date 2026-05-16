import pytest
from core.source_manager import (
    load_sources,
    save_sources,
    add_source,
    get_source_count,
    get_sources_by_type,
    check_distribution,
)


def test_load_sources_returns_empty_when_file_missing(tmp_data_dir):
    (tmp_data_dir / "sources.json").unlink()
    assert load_sources() == []


def test_load_sources_raises_on_corrupt_file(tmp_data_dir):
    import config
    config.SOURCES_FILE.write_text("not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_sources()


def test_add_source_creates_file_and_assigns_id(tmp_data_dir, sample_sources):
    src = sample_sources[0].copy()
    src.pop("id")
    add_source(src)
    sources = load_sources()
    assert len(sources) == 1
    assert sources[0]["id"] == "src_001"


def test_add_source_skips_duplicate_url(tmp_data_dir, sample_sources):
    src = sample_sources[0].copy()
    src.pop("id")
    add_source(src)
    add_source(src)
    assert get_source_count() == 1


def test_add_source_increments_id(tmp_data_dir, sample_sources):
    for src in sample_sources:
        s = src.copy()
        s.pop("id")
        add_source(s)
    sources = load_sources()
    assert sources[0]["id"] == "src_001"
    assert sources[1]["id"] == "src_002"


def test_get_sources_by_type(tmp_data_dir, sample_sources):
    for src in sample_sources:
        s = src.copy()
        s.pop("id")
        add_source(s)
    scientific = get_sources_by_type("scientific")
    assert len(scientific) == 1
    assert scientific[0]["type"] == "scientific"


def test_check_distribution_warns_when_below_minimum(tmp_data_dir, sample_sources):
    for src in sample_sources:
        s = src.copy()
        s.pop("id")
        add_source(s)
    result = check_distribution()
    assert len(result["warnings"]) > 0
    assert any("scientific" in w for w in result["warnings"])


def test_check_distribution_no_warnings_when_met(tmp_data_dir):
    for i in range(3):
        add_source({"author": f"Auth{i}", "title": f"Sci{i}", "year": 2020,
                    "publisher": "J", "url": f"https://sci{i}.com",
                    "summary": "s", "key_quotes": [], "type": "scientific"})
    for i in range(2):
        add_source({"author": "", "title": f"Law{i}", "year": 2020,
                    "publisher": "EU", "url": f"https://law{i}.eu",
                    "summary": "s", "key_quotes": [], "type": "legal"})
    result = check_distribution()
    assert result["warnings"] == []
