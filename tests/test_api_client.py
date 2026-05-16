import pytest
from unittest.mock import MagicMock, patch
from core.api_client import call, call_with_tools


def _make_response(text: str, stop_reason: str = "end_turn"):
    block = MagicMock()
    block.text = text
    block.type = "text"
    resp = MagicMock()
    resp.content = [block]
    resp.stop_reason = stop_reason
    return resp


def test_call_returns_text(monkeypatch):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response("Hello world")
    with patch("core.api_client._get_client", return_value=mock_client):
        result = call(system="sys", user="usr", mode="write")
    assert result == "Hello world"


def test_call_uses_correct_temperature(monkeypatch):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response("ok")
    with patch("core.api_client._get_client", return_value=mock_client):
        call(system="sys", user="usr", mode="evaluate")
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["temperature"] == 0.1


def test_call_with_cache_adds_cache_control(monkeypatch):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response("ok")
    with patch("core.api_client._get_client", return_value=mock_client):
        call(system="sys", user="usr", mode="write", use_cache=True)
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_call_without_cache_has_no_cache_control(monkeypatch):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response("ok")
    with patch("core.api_client._get_client", return_value=mock_client):
        call(system="sys", user="usr", mode="write", use_cache=False)
    kwargs = mock_client.messages.create.call_args.kwargs
    assert "cache_control" not in kwargs["system"][0]


def test_call_with_tools_handles_end_turn(monkeypatch):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response("result")
    with patch("core.api_client._get_client", return_value=mock_client):
        result = call_with_tools(system="sys", user="usr", tools=[])
    assert result == "result"


def test_call_with_tools_loops_on_tool_use(monkeypatch):
    mock_client = MagicMock()
    tool_use_resp = _make_response("intermediate", stop_reason="tool_use")
    final_resp = _make_response("final result")
    mock_client.messages.create.side_effect = [tool_use_resp, final_resp]
    with patch("core.api_client._get_client", return_value=mock_client):
        result = call_with_tools(system="sys", user="usr", tools=[])
    assert result == "final result"
    assert mock_client.messages.create.call_count == 2
