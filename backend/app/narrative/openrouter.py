"""Thin OpenRouter API client with retry, timeout, and cost logging."""
from __future__ import annotations

import time
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

# Rough cost estimate for DeepSeek V3 via OpenRouter ($/1M tokens, 2025)
_INPUT_COST_PER_1M = 0.27
_OUTPUT_COST_PER_1M = 1.10


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Return the assistant content string from the LLM."""
    m = model or settings.openrouter_model
    t = temperature if temperature is not None else settings.llm_temperature
    n = max_tokens or settings.llm_max_tokens

    payload: dict[str, Any] = {
        "model": m,
        "messages": messages,
        "temperature": t,
        "max_tokens": n,
    }

    start = time.monotonic()
    with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
        resp = client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "HTTP-Referer": settings.base_url,
                "X-Title": settings.app_name,
            },
            json=payload,
        )
        resp.raise_for_status()

    elapsed = time.monotonic() - start
    data = resp.json()
    usage = data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    cost_usd = (
        input_tokens / 1_000_000 * _INPUT_COST_PER_1M
        + output_tokens / 1_000_000 * _OUTPUT_COST_PER_1M
    )

    log.info(
        "llm.call",
        model=m,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=round(cost_usd, 6),
        latency_s=round(elapsed, 2),
    )

    return data["choices"][0]["message"]["content"].strip()
