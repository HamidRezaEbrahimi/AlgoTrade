# app/ai_agent/llm_client.py
"""
Async LLM Client for Google Generative Language API (Gemini).

Model name and API key are read from Settings — nothing is hardcoded.
Includes exponential-backoff retry, timeout, and rate limiting.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger("algotrade.ai_agent.llm_client")

# Rate limit: minimum seconds between consecutive API calls
_MIN_REQUEST_INTERVAL_SEC = 2.0

# Gemini Generative Language API base
_GEMINI_API_BASE = (
    "https://generativelanguage.googleapis.com/v1beta/models"
)


class LLMClient:
    """Async client for Google Gemini Generative Language API.

    Reads model name and API key at construction time from the
    caller (typically ``Settings``).  Nothing is hardcoded.
    """

    def __init__(
        self,
        api_key: str = "",
        model_name: str = "gemini-2.5-flash-lite",
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self._last_request_ts: float = 0.0
        self._lock = asyncio.Lock()

    # ── Public API ───────────────────────────────────────

    @property
    def is_configured(self) -> bool:
        """True when an API key has been provided."""
        return bool(self.api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        response_json: bool = False,
    ) -> str:
        """Send a prompt to Gemini and return the text response.

        Args:
            prompt: User-level prompt text.
            system_prompt: Optional system-level instruction.
            response_json: If True, ask the model to produce JSON output.

        Returns:
            Model-generated text, or empty string on failure.
        """
        if not self.is_configured:
            logger.debug("LLM client not configured (no API key)")
            return ""

        url = (
            f"{_GEMINI_API_BASE}/{self.model_name}:generateContent"
            f"?key={self.api_key}"
        )

        body = self._build_request_body(
            prompt, system_prompt, response_json,
        )

        return await self._call_with_retry(url, body)

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> dict[str, Any] | None:
        """Generate and parse a JSON response from the LLM.

        Returns parsed dict on success, ``None`` on failure or parse error.
        """
        raw = await self.generate(
            prompt, system_prompt, response_json=True,
        )
        if not raw:
            return None
        return self._parse_json_response(raw)

    # ── Internal Helpers ─────────────────────────────────

    @staticmethod
    def _build_request_body(
        prompt: str,
        system_prompt: str,
        response_json: bool,
    ) -> dict[str, Any]:
        """Build the Gemini generateContent request payload."""
        contents = []

        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"[System Instruction]\n{system_prompt}"}],
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will follow these instructions."}],
            })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt}],
        })

        body: dict[str, Any] = {"contents": contents}

        generation_config: dict[str, Any] = {
            "temperature": 0.3,
            "maxOutputTokens": 2048,
        }
        if response_json:
            generation_config["responseMimeType"] = "application/json"
        body["generationConfig"] = generation_config

        return body

    async def _call_with_retry(
        self, url: str, body: dict[str, Any],
    ) -> str:
        """Execute HTTP POST with rate limiting and exponential backoff."""
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            # Rate limiting
            await self._enforce_rate_limit()

            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout),
                ) as client:
                    resp = await client.post(
                        url,
                        json=body,
                        headers={"Content-Type": "application/json"},
                    )

                if resp.status_code == 429:
                    wait = min(30, 2 ** attempt * 5)
                    logger.warning(
                        "Gemini rate-limited (429), retrying in %ds "
                        "(attempt %d/%d)",
                        wait, attempt, self.max_retries,
                    )
                    await asyncio.sleep(wait)
                    continue

                if resp.status_code >= 400:
                    logger.error(
                        "Gemini API error %d: %s",
                        resp.status_code,
                        resp.text[:300],
                    )
                    last_error = httpx.HTTPStatusError(
                        f"Status {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )
                    if attempt < self.max_retries:
                        await asyncio.sleep(2 ** attempt)
                    continue

                # Success — extract text
                data = resp.json()
                return self._extract_text(data)

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc
                logger.warning(
                    "Gemini request failed (attempt %d/%d): %s",
                    attempt, self.max_retries, exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)

        logger.error(
            "All %d Gemini attempts failed: %s",
            self.max_retries, last_error,
        )
        return ""

    async def _enforce_rate_limit(self) -> None:
        """Ensure minimum interval between requests."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_ts
            if elapsed < _MIN_REQUEST_INTERVAL_SEC:
                await asyncio.sleep(
                    _MIN_REQUEST_INTERVAL_SEC - elapsed,
                )
            self._last_request_ts = time.monotonic()

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        """Extract generated text from Gemini response payload."""
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            texts = [p.get("text", "") for p in parts if "text" in p]
            return "".join(texts).strip()
        except (KeyError, IndexError, TypeError) as exc:
            logger.warning("Failed to extract text from Gemini: %s", exc)
            return ""

    @staticmethod
    def _parse_json_response(raw: str) -> dict[str, Any] | None:
        """Best-effort JSON extraction from model output."""
        raw = raw.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = [
                ln for ln in lines
                if not ln.strip().startswith("```")
            ]
            raw = "\n".join(lines).strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Try to find a JSON object within the text
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse JSON from LLM output: %.200s", raw)
        return None
