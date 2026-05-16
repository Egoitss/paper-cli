import pytest
import yaml


@pytest.fixture
def papers_env(tmp_path, monkeypatch):
    import core.paper_manager as pm
    papers = tmp_path / "papers"
    papers.mkdir()
    active_file = tmp_path / ".active_paper"
    monkeypatch.setattr(pm, "PAPERS_DIR", papers)
    monkeypatch.setattr(pm, "ACTIVE_PAPER_FILE", active_file)
    return tmp_path


def _make_paper(papers_dir, name: str, title: str = "Test Paper"):
    p = papers_dir / name
    p.mkdir()
    (p / "data" / "chapters").mkdir(parents=True)
    (p / "data" / "appendices").mkdir(parents=True)
    (p / "data" / "sources.json").write_text("[]", encoding="utf-8")
    (p / "paper.yaml").write_text(
        f'title: "{title}"\n'
        "sections:\n"
        "  - id: introduction\n"
        '    title: "Introduction"\n'
        '    heading: "INTRODUCTION"\n'
        "    target_words: [500, 800]\n"
        "    kind: introduction\n"
        "  - id: chapter_1\n"
        '    title: "Chapter 1"\n'
        '    heading: "CHAPTER 1"\n'
        "    target_words: [600, 900]\n"
        "    kind: subchapter\n"
        "    chapter: 1\n"
        "chapter_headings:\n"
        '  1: "FIRST CHAPTER"\n'
        "features:\n"
        "  bibliography: true\n"
        "  appendices: false\n",
        encoding="utf-8",
    )
    return p


def test_get_active_paper_name_returns_name(papers_env):
    import core.paper_manager as pm
    (papers_env / ".active_paper").write_text("my_paper", encoding="utf-8")
    assert pm.get_active_paper_name() == "my_paper"


def test_get_active_paper_name_returns_none_when_no_file(papers_env):
    import core.paper_manager as pm
    assert pm.get_active_paper_name() is None


def test_get_active_paper_name_returns_none_for_empty_file(papers_env):
    import core.paper_manager as pm
    (papers_env / ".active_paper").write_text("  ", encoding="utf-8")
    assert pm.get_active_paper_name() is None


def test_load_active_paper_returns_none_when_no_active(papers_env):
    import core.paper_manager as pm
    assert pm.load_active_paper() is None


def test_load_active_paper_returns_parsed_config(papers_env):
    import core.paper_manager as pm
    _make_paper(papers_env / "papers", "my_paper", "My Title")
    (papers_env / ".active_paper").write_text("my_paper", encoding="utf-8")
    result = pm.load_active_paper()
    assert result["title"] == "My Title"
    assert result["name"] == "my_paper"
    assert result["sections"] == ["introduction", "chapter_1"]
    assert isinstance(result["section_meta"]["introduction"]["target_words"], tuple)
    assert result["section_meta"]["introduction"]["target_words"] == (500, 800)
    assert result["section_meta"]["chapter_1"].get("chapter") == 1
    assert result["chapter_headings"] == {1: "FIRST CHAPTER"}
    assert result["features"] == {"bibliography": True, "appendices": False, "require_scientific": True}


def test_load_active_paper_data_dir_points_inside_paper(papers_env):
    import core.paper_manager as pm
    _make_paper(papers_env / "papers", "my_paper")
    (papers_env / ".active_paper").write_text("my_paper", encoding="utf-8")
    result = pm.load_active_paper()
    assert result["data_dir"] == papers_env / "papers" / "my_paper" / "data"
    assert result["paper_dir"] == papers_env / "papers" / "my_paper"


def test_activate_paper_writes_active_file(papers_env):
    import core.paper_manager as pm
    _make_paper(papers_env / "papers", "my_paper")
    pm.activate_paper("my_paper")
    assert (papers_env / ".active_paper").read_text(encoding="utf-8") == "my_paper"


def test_activate_paper_raises_for_missing_paper(papers_env):
    import core.paper_manager as pm
    with pytest.raises(ValueError, match="not found"):
        pm.activate_paper("nonexistent")


def test_create_paper_creates_directory_structure(papers_env):
    import core.paper_manager as pm
    pm.create_paper("new_paper", "New Paper Title")
    paper_dir = papers_env / "papers" / "new_paper"
    assert (paper_dir / "data" / "chapters").exists()
    assert (paper_dir / "data" / "appendices").exists()
    assert (paper_dir / "data" / "sources.json").read_text(encoding="utf-8") == "[]"


def test_create_paper_writes_valid_yaml(papers_env):
    import core.paper_manager as pm
    pm.create_paper("new_paper", "New Paper Title")
    path = papers_env / "papers" / "new_paper" / "paper.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert cfg["title"] == "New Paper Title"
    assert len(cfg["sections"]) >= 2
    assert all("id" in s and "target_words" in s and "kind" in s for s in cfg["sections"])


def test_create_paper_raises_if_already_exists(papers_env):
    import core.paper_manager as pm
    _make_paper(papers_env / "papers", "existing")
    with pytest.raises(ValueError, match="already exists"):
        pm.create_paper("existing", "Title")


def test_list_papers_returns_sorted_names(papers_env):
    import core.paper_manager as pm
    _make_paper(papers_env / "papers", "paper_b")
    _make_paper(papers_env / "papers", "paper_a")
    assert pm.list_papers() == ["paper_a", "paper_b"]


def test_list_papers_excludes_dirs_without_yaml(papers_env):
    import core.paper_manager as pm
    _make_paper(papers_env / "papers", "paper_a")
    (papers_env / "papers" / "stray_dir").mkdir()
    assert pm.list_papers() == ["paper_a"]


def test_list_papers_returns_empty_when_no_papers_dir(papers_env):
    import core.paper_manager as pm
    import shutil
    shutil.rmtree(papers_env / "papers")
    assert pm.list_papers() == []


def test_load_paper_yaml_raises_for_missing_file(papers_env):
    import core.paper_manager as pm
    with pytest.raises(ValueError, match="has no paper.yaml"):
        pm.load_paper_yaml("ghost_paper")


def test_load_paper_yaml_raises_for_invalid_yaml(papers_env):
    import core.paper_manager as pm
    (papers_env / "papers" / "bad").mkdir()
    (papers_env / "papers" / "bad" / "paper.yaml").write_text(
        "title: [unclosed", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="is not valid YAML"):
        pm.load_paper_yaml("bad")


def test_create_paper_handles_quoted_title(papers_env):
    import core.paper_manager as pm
    import yaml
    pm.create_paper("q_paper", 'My "Great" Paper')
    path = papers_env / "papers" / "q_paper" / "paper.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert cfg["title"] == 'My "Great" Paper'
