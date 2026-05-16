import re
import config

# Parses lines like `- [x] chapter_1_1` from project_state.md
_STATUS_RE = re.compile(r"^- \[([x~ ])\] (\S+)$", re.MULTILINE)
# Maps human-readable status names to the single character used in the file
_MARK = {"approved": "x", "drafted": "~", "pending": " "}
_STATUS = {"x": "approved", "~": "drafted", " ": "pending"}


def load_state() -> dict[str, str]:
    # Seeds every section as pending, then overlays values found in the file;
    # sections not yet in the file stay pending
    state = {s: "pending" for s in config.SECTIONS}
    if not config.STATE_FILE.exists():
        return state
    for m in _STATUS_RE.finditer(config.STATE_FILE.read_text(encoding="utf-8")):
        section = m.group(2)
        if section in state:
            state[section] = _STATUS[m.group(1)]
    return state


def save_state(state: dict[str, str]) -> None:
    # Always writes sections in config.SECTIONS order, not in input-dict order,
    # so the file is deterministic regardless of how state was built
    config.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Project State\n\n",
        "Legend: `[ ]` pending | `[~]` drafted | `[x]` approved\n\n",
    ]
    for section in config.SECTIONS:
        status = state.get(section, "pending")
        if status not in _MARK:
            status = "pending"
        mark = _MARK[status]
        lines.append(f"- [{mark}] {section}\n")
    config.STATE_FILE.write_text("".join(lines), encoding="utf-8")


def mark_drafted(section: str) -> None:
    if section not in config.SECTIONS:
        raise ValueError(f"Unknown section: '{section}'. Valid: {config.SECTIONS}")
    state = load_state()
    state[section] = "drafted"
    save_state(state)


def mark_approved(section: str) -> None:
    if section not in config.SECTIONS:
        raise ValueError(f"Unknown section: '{section}'. Valid: {config.SECTIONS}")
    state = load_state()
    state[section] = "approved"
    save_state(state)


def get_pending_sections() -> list[str]:
    state = load_state()
    return [s for s in config.SECTIONS if state[s] == "pending"]


def get_approved_sections() -> list[str]:
    state = load_state()
    return [s for s in config.SECTIONS if state[s] == "approved"]
