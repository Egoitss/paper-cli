import json
import pytest
from core.prompt_builder import (
    build_system,
    build_write_prompt,
    build_evaluate_prompt,
    build_evaluate_system,
    build_research_prompt,
)


def test_build_system_contains_xml_tags(tmp_data_dir):
    result = build_system()
    assert "<system>" in result
    assert "<role>" in result
    assert "<project>" in result
    assert "<state>" in result


def test_build_system_with_sources_contains_sources(tmp_data_dir, sample_sources):
    from core.source_manager import save_sources
    save_sources(sample_sources)
    result = build_system(include_sources=True)
    assert "<sources>" in result
    assert "src_001" in result


def test_build_write_prompt_introduction_contains_all_6_elements(tmp_data_dir):
    prompt = build_write_prompt("introduction", ["src_001"])
    assert "relevance" in prompt.lower()
    assert "prior research" in prompt.lower()
    assert "goal" in prompt.lower()
    assert "scope" in prompt.lower()
    assert "research methods" in prompt.lower()


def test_build_write_prompt_subchapter_requires_conclusions_paragraph(tmp_data_dir):
    prompt = build_write_prompt("chapter_1_1", ["src_001"])
    assert "conclusions paragraph" in prompt.lower()


def test_build_write_prompt_conclusions_requires_proposals(tmp_data_dir):
    prompt = build_write_prompt("conclusions", ["src_001"])
    assert "proposals" in prompt.lower()
    assert "recommendations" in prompt.lower()


def test_build_evaluate_system_contains_all_criteria(tmp_data_dir, monkeypatch):
    import config
    monkeypatch.setitem(config.FEATURES, "require_scientific", True)
    system = build_evaluate_system("chapter_1_1")
    assert "word_count" in system
    assert "sources_cited" in system
    assert "scientific_sources" in system
    assert "tone" in system
    assert "<system>" in system
    assert "<user>" not in system


def test_build_evaluate_prompt_contains_draft_and_task(tmp_data_dir):
    prompt = build_evaluate_prompt("part_1", "Some draft text here.")
    assert "<user>" in prompt
    assert "Some draft text here." in prompt
    assert "<system>" not in prompt
    assert "<criteria>" not in prompt


def test_build_research_prompt_contains_type_instruction(tmp_data_dir):
    prompt = build_research_prompt("sample topic", "scientific", [])
    assert "peer-reviewed" in prompt.lower()
    assert "JSON" in prompt


def test_build_write_prompt_citation_format_instruction(tmp_data_dir):
    prompt = build_write_prompt("chapter_1_2", ["src_001", "src_002"])
    assert "cite:" in prompt
