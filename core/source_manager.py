import json
import config


def _next_id(sources: list[dict]) -> str:
    # Finds the highest existing src_NNN number and increments it;
    # starts at src_001 if the list is empty
    existing = [
        int(s["id"].split("_")[1])
        for s in sources
        if s.get("id", "").startswith("src_")
    ]
    return f"src_{(max(existing) + 1) if existing else 1:03d}"


def load_sources() -> list[dict]:
    if not config.SOURCES_FILE.exists():
        return []
    try:
        return json.loads(config.SOURCES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"sources.json is not valid JSON: {exc}") from exc


def save_sources(sources: list[dict]) -> None:
    config.SOURCES_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.SOURCES_FILE.write_text(
        json.dumps(sources, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def add_source(source: dict) -> None:
    # Deduplicates by URL — if a source with the same URL already exists, silently skips
    sources = load_sources()
    if any(s["url"] == source["url"] for s in sources):
        return
    new_source = {**source, "id": _next_id(sources)}
    sources.append(new_source)
    save_sources(sources)


def get_source_count() -> int:
    return len(load_sources())


def get_sources_by_type(source_type: str) -> list[dict]:
    return [s for s in load_sources() if s.get("type") == source_type]


def check_distribution() -> dict[str, list]:
    # Validates that mandatory source types meet the minimums defined in config.SOURCE_MINIMUMS
    sources = load_sources()
    counts: dict[str, int] = {}
    for s in sources:
        t = s.get("type", "general")
        counts[t] = counts.get(t, 0) + 1

    warnings = []
    for stype, minimum in config.SOURCE_MINIMUMS.items():
        current = counts.get(stype, 0)
        if current < minimum:
            warnings.append(
                f"Need {minimum - current} more {stype} source(s) "
                f"(have {current}, need {minimum})"
            )
    return {"counts": counts, "warnings": warnings}
