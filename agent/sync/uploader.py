"""HTTPS uploader — sends the encrypted financial snapshot to the Ghost CFO API.

Retries up to 3 times with exponential back-off on transient failures.
Raises on non-retryable HTTP errors (4xx) so the caller can log and abort.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx

log = logging.getLogger(__name__)

_TIMEOUT = 30  # seconds per request


def upload_snapshot(
    payload_b64: str,
    api_key: str,
    base_url: str,
    max_retries: int = 3,
) -> dict[str, Any]:
    """POST the encrypted payload to ``<base_url>/agent/ingest``.

    Args:
        payload_b64: Base64-encoded AES-GCM envelope from encryptor.
        api_key:     Per-client API key (sent as ``X-Agent-Key`` header).
        base_url:    Ghost CFO backend root, e.g. ``https://ghostcfo.numbers10.co.za``.
        max_retries: How many attempts before giving up.

    Returns:
        Parsed JSON response body from the backend.

    Raises:
        httpx.HTTPStatusError: On 4xx (non-retryable) errors.
        RuntimeError: If all retry attempts are exhausted on 5xx / network errors.
    """
    url = base_url.rstrip("/") + "/api/agent/ingest"
    headers = {
        "X-Agent-Key": api_key,
        "Content-Type": "application/json",
        "User-Agent": "GhostCFOAgent/1.0",
    }
    body = {"payload": payload_b64}

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=_TIMEOUT, verify=True) as client:
                response = client.post(url, json=body, headers=headers)

            if response.status_code < 400:
                log.info("Upload succeeded on attempt %d (HTTP %d)", attempt, response.status_code)
                return response.json()

            if 400 <= response.status_code < 500:
                # Client error — no point retrying
                log.error("Upload rejected (HTTP %d): %s", response.status_code, response.text[:200])
                response.raise_for_status()

            # 5xx — retryable
            log.warning(
                "Upload failed with HTTP %d on attempt %d/%d",
                response.status_code, attempt, max_retries,
            )
            last_exc = httpx.HTTPStatusError(
                f"HTTP {response.status_code}", request=response.request, response=response
            )

        except httpx.TimeoutException as exc:
            log.warning("Upload timed out on attempt %d/%d: %s", attempt, max_retries, exc)
            last_exc = exc
        except httpx.ConnectError as exc:
            log.warning("Upload connection error on attempt %d/%d: %s", attempt, max_retries, exc)
            last_exc = exc

        if attempt < max_retries:
            wait = 15 * (2 ** (attempt - 1))  # 15s, 30s
            log.info("Retrying in %ds…", wait)
            time.sleep(wait)

    raise RuntimeError(
        f"Upload failed after {max_retries} attempts. Last error: {last_exc}"
    ) from last_exc
