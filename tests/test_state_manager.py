import pytest
from core.state_manager import (
    load_state,
    save_state,
    mark_drafted,
    mark_approved,
    get_pending_sections,
    get_approved_sections,
)
from config import SECTIONS


def test_load_state_returns_all_pending_when_file_missing(tmp_data_dir):
    state = load_state()
    assert all(v == "pending" for v in state.values())
    assert set(state.keys()) == set(SECTIONS)


def test_mark_drafted_updates_state(tmp_data_dir):
    mark_drafted("introduction")
    state = load_state()
    assert state["introduction"] == "drafted"
    assert state["chapter_1_1"] == "pending"


def test_mark_approved_updates_state(tmp_data_dir):
    mark_drafted("introduction")
    mark_approved("introduction")
    state = load_state()
    assert state["introduction"] == "approved"


def test_state_persists_across_load(tmp_data_dir):
    mark_drafted("chapter_1_1")
    mark_approved("chapter_1_1")
    mark_drafted("chapter_1_2")
    state = load_state()
    assert state["chapter_1_1"] == "approved"
    assert state["chapter_1_2"] == "drafted"
    assert state["chapter_2_1"] == "pending"


def test_get_pending_sections(tmp_data_dir):
    mark_approved("introduction")
    pending = get_pending_sections()
    assert "introduction" not in pending
    assert "chapter_1_1" in pending


def test_get_approved_sections(tmp_data_dir):
    mark_approved("introduction")
    mark_approved("chapter_1_1")
    approved = get_approved_sections()
    assert approved == ["introduction", "chapter_1_1"]


def test_mark_drafted_raises_on_unknown_section(tmp_data_dir):
    with pytest.raises(ValueError, match="Unknown section"):
        mark_drafted("nonexistent_section")


def test_mark_approved_raises_on_unknown_section(tmp_data_dir):
    with pytest.raises(ValueError, match="Unknown section"):
        mark_approved("nonexistent_section")
