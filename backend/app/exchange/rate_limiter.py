# app/exchange/rate_limiter.py
"""
Exchange API Rate Limiter & Resilience Handler.

Rules:
- Minimum 12 seconds interval between consecutive API requests.
- Maximum 3 retries on Rate Limit (HTTP 429) errors with a 30-second pause.
- Exponential backoff on transient network failures.
"""
from __future__ import annotations

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger("algotrade.exchange.rate_limiter")

T = TypeVar("T")


class AsyncRateLimiter:
    """Token bucket / interval rate limiter for async API calls."""

    def __init__(self, min_interval_seconds: float = 12.0) -> None:
        self.min_interval = min_interval_seconds
        self._last_call_time = 0.0
        self._lock = asyncio.Lock()

    async def wait_for_slot(self) -> None:
        """Enforce minimum delay between calls."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call_time
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                logger.debug(f"RateLimiter: waiting {wait_time:.2f}s before next API request...")
                await asyncio.sleep(wait_time)
            self._last_call_time = time.monotonic()


def with_exchange_retry(
    max_retries: int = 3,
    rate_limit_pause_sec: float = 30.0,
    backoff_factor: float = 2.0,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for robust exchange API calls:
    - On 429 (Rate Limit): Pauses for 30s, up to 3 retries.
    - On Network/Timeout: Exponential backoff.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_err: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    err_str = str(e).lower()
                    if "401" in err_str or "unauthorized" in err_str or "403" in err_str or "forbidden" in err_str:
                        raise e

                    is_rate_limit = "429" in err_str or "rate limit" in err_str or "too many requests" in err_str

                    if attempt < max_retries:
                        if is_rate_limit:
                            logger.warning(
                                f"⚠️ Rate limit hit on {func.__name__}! "
                                f"Pausing for {rate_limit_pause_sec}s (Attempt {attempt+1}/{max_retries})."
                            )
                            await asyncio.sleep(rate_limit_pause_sec)
                        else:
                            sleep_time = backoff_factor ** attempt
                            logger.warning(
                                f"⚠️ Transient error on {func.__name__}: {e}. "
                                f"Retrying in {sleep_time:.1f}s (Attempt {attempt+1}/{max_retries})."
                            )
                            await asyncio.sleep(sleep_time)
                    else:
                        logger.error(f"❌ Max retries ({max_retries}) reached for {func.__name__}.")

            raise last_err or RuntimeError("Exchange call failed without exception.")
        return wrapper
    return decorator
