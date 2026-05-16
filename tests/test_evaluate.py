import json
import pytest
from unittest.mock import patch
from commands.evaluate import evaluate, EvalResult


_PASS_RESPONSE = json.dumps({"pass": True, "failures": [], "word_count": 750})
_FAIL_RESPONSE = json.dumps({
    "pass": False,
    "failures": [{"criterion": "tone", "detail": "Uses first person 'I'"}],
    "word_count": 400,
})


def test_evaluate_returns_pass_result(tmp_data_dir):
    with patch("commands.evaluate._call_evaluator", return_value=_PASS_RESPONSE):
        result = evaluate("chapter_1_1", "Some academic draft text here.")
    assert result.passed is True
    assert result.failures == []
    assert result.word_count == 750


def test_evaluate_returns_fail_result(tmp_data_dir):
    with patch("commands.evaluate._call_evaluator", return_value=_FAIL_RESPONSE):
        result = evaluate("chapter_1_1", "I think AI is good.")
    assert result.passed is False
    assert len(result.failures) == 1
    assert result.failures[0]["criterion"] == "tone"


def test_evaluate_handles_malformed_json(tmp_data_dir):
    with patch("commands.evaluate._call_evaluator", return_value="not json"):
        result = evaluate("chapter_1_1", "Some text.")
    assert result.passed is False
    assert any("parse" in f["detail"].lower() for f in result.failures)
