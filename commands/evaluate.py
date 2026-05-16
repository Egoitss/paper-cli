from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
import config
from core.api_client import call
from core.prompt_builder import build_evaluate_prompt, build_evaluate_system


@dataclass
class EvalResult:
    passed: bool
    failures: list[dict] = field(default_factory=list)
    word_count: int = 0


def _call_evaluator(section: str, draft: str) -> str:
    system = build_evaluate_system(section)
    user = build_evaluate_prompt(section, draft)
    return call(system=system, user=user, mode="evaluate")


def evaluate(section: str, draft: str) -> EvalResult:
    raw = _call_evaluator(section, draft)

    # Find first { and match balanced braces to handle nested objects
    start = raw.find('{')
    if start == -1:
        return EvalResult(
            passed=False,
            failures=[{"criterion": "parse", "detail": "Could not parse evaluator response"}],
        )

    depth = 0
    in_string = False
    escape_next = False

    for i in range(start, len(raw)):
        ch = raw[i]
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    json_str = raw[start:i+1]
                    try:
                        data = json.loads(json_str)
                        return EvalResult(
                            passed=bool(data.get("pass", False)),
                            failures=data.get("failures", []),
                            word_count=data.get("word_count", 0),
                        )
                    except json.JSONDecodeError:
                        return EvalResult(
                            passed=False,
                            failures=[{"criterion": "parse", "detail": "Malformed JSON from evaluator"}],
                        )

    return EvalResult(
        passed=False,
        failures=[{"criterion": "parse", "detail": "Could not parse evaluator response"}],
    )
