from __future__ import annotations
from typing import Optional
import time
import anthropic
import config

# Lazy singleton — one client instance reused across all calls in the process
_client: Optional[anthropic.Anthropic] = None


def _get_client() -> "anthropic.Anthropic":
    # Initialised on first call so tests can set ANTHROPIC_API_KEY before import
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.API_KEY)
    return _client


def _with_backoff(fn, max_retries: int = 5):
    # Starts at 60 s because the API rate-limit window is typically 1 minute;
    # doubles each retry up to a 5-minute ceiling
    delay = 60
    for attempt in range(max_retries):
        try:
            return fn()
        except anthropic.RateLimitError:
            if attempt == max_retries - 1:
                raise
            print(f"[rate limit] waiting {delay}s before retry {attempt + 2}/{max_retries}…")
            time.sleep(delay)
            delay = min(delay * 2, 300)


def call(
    system: str,
    user: str,
    mode: str,
    use_cache: bool = False,
) -> str:
    # Single-turn completion; mode selects the temperature from config.TEMPERATURE
    client = _get_client()
    system_block: dict = {"type": "text", "text": system}
    if use_cache:
        # Ephemeral cache_control pins the system block in the prompt cache
        # for the 5-minute TTL, reducing cost on repeated calls with the same system
        system_block["cache_control"] = {"type": "ephemeral"}

    def _do():
        response = client.messages.create(
            model=config.MODEL,
            max_tokens=4096,
            temperature=config.TEMPERATURE[mode],
            system=[system_block],
            messages=[{"role": "user", "content": user}],
        )
        return _extract_text(response.content)

    return _with_backoff(_do)


def call_with_tools(
    system: str,
    user: str,
    tools: list[dict],
    mode: str = "research",
) -> str:
    # Agentic loop: model may call tools multiple times before producing a final answer
    client = _get_client()
    messages: list[dict] = [{"role": "user", "content": user}]

    for _ in range(8):
        # Capture messages in default arg to avoid closure-over-loop-variable bug
        def _do(msgs=messages):
            return client.messages.create(
                model=config.MODEL,
                max_tokens=8192,
                temperature=config.TEMPERATURE[mode],
                system=[{"type": "text", "text": system}],
                tools=tools,
                messages=msgs,
            )

        response = _with_backoff(_do)
        if response.stop_reason == "end_turn":
            # Model finished without requesting another tool call
            return _extract_text(response.content)
        # Append assistant turn and nudge to continue
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": "Continue and provide the final result."})

    # Fallback: return whatever text the model produced on the last iteration
    return _extract_text(response.content)


def _extract_text(content: list) -> str:
    # Skips tool_use blocks; only concatenates text blocks from the response
    return "\n".join(b.text for b in content if hasattr(b, "text"))
