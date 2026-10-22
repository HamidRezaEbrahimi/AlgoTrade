# app/market_data/sentiment_feed.py
"""
Social Sentiment Feed — LunarCrush integration.

Fetches social media sentiment data for crypto assets and normalizes
it to a 0–100 score.  In-memory cache prevents excessive API calls.
Falls back to neutral data when no API key is configured.

Provider and API key are read from Settings — nothing is hardcoded.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.config import get_settings
from app.market_data.sentiment_models import SentimentData

logger = logging.getLogger("algotrade.market_data.sentiment")

# LunarCrush API v4 base
_LUNARCRUSH_BASE = "https://lunarcrush.com/api4/public/coins"

# Symbol normalization: remove USDT/USD suffixes for LunarCrush
_STRIP_SUFFIXES = ("USDT", "BUSD", "USDC", "USD", "IRT", "TMN")


class SentimentFeed:
    """Abstract base for sentiment data providers."""

    async def get_social_metrics(self, symbol: str) -> SentimentData:
        """Fetch normalized sentiment data for a symbol."""
        raise NotImplementedError


class NullSentimentFeed(SentimentFeed):
    """Fallback provider returning neutral sentiment (score=50)."""

    async def get_social_metrics(self, symbol: str) -> SentimentData:
        return SentimentData.neutral(_normalize_symbol(symbol))


class LunarCrushFeed(SentimentFeed):
    """LunarCrush API v4 sentiment data provider with in-memory cache."""

    def __init__(
        self,
        api_key: str = "",
        cache_ttl_minutes: int = 15,
        timeout_seconds: int = 15,
    ) -> None:
        self.api_key = api_key
        self.cache_ttl = cache_ttl_minutes * 60  # seconds
        self.timeout = timeout_seconds
        self._cache: dict[str, _CacheEntry] = {}

    async def get_social_metrics(self, symbol: str) -> SentimentData:
        """Fetch social sentiment for a crypto symbol.

        Uses in-memory cache with configurable TTL.
        Returns neutral data on any error.
        """
        clean_sym = _normalize_symbol(symbol)

        # Check cache
        cached = self._get_cached(clean_sym)
        if cached is not None:
            return cached

        # Fetch from API
        data = await self._fetch_from_api(clean_sym)
        self._set_cache(clean_sym, data)
        return data

    def clear_cache(self) -> None:
        """Clear the entire sentiment cache."""
        self._cache.clear()

    # ── Private: API Communication ───────────────────────

    async def _fetch_from_api(self, symbol: str) -> SentimentData:
        """Call LunarCrush API and return normalized sentiment."""
        if not self.api_key:
            logger.debug(
                "LunarCrush API key not configured, returning neutral",
            )
            return SentimentData.neutral(symbol)

        url = f"{_LUNARCRUSH_BASE}/{symbol}/v1"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
            ) as client:
                resp = await client.get(url, headers=headers)

            if resp.status_code == 404:
                logger.info(
                    "LunarCrush: symbol %s not found (404)", symbol,
                )
                return SentimentData.neutral(symbol)

            if resp.status_code == 429:
                logger.warning("LunarCrush rate-limited (429)")
                return SentimentData.neutral(symbol)

            if resp.status_code >= 400:
                logger.error(
                    "LunarCrush API error %d: %s",
                    resp.status_code,
                    resp.text[:200],
                )
                return SentimentData.neutral(symbol)

            raw = resp.json()
            return self._parse_response(symbol, raw)

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning("LunarCrush request failed: %s", exc)
            return SentimentData.neutral(symbol)

    @staticmethod
    def _parse_response(
        symbol: str, raw: dict[str, Any],
    ) -> SentimentData:
        """Parse LunarCrush API response into SentimentData."""
        # LunarCrush v4 wraps data in a "data" key
        data = raw.get("data", raw)

        galaxy_score = float(data.get("galaxy_score", 50))
        alt_rank = int(data.get("alt_rank", 500))
        mentions = int(data.get("social_mentions", 0))
        interactions = int(data.get("social_interactions", 0))
        creators = int(data.get("social_contributors", 0))

        # Compute normalized score (0–100):
        # 70% galaxy_score + 30% inverted alt_rank
        alt_rank_clamped = max(1, min(alt_rank, 1000))
        alt_score = (1 - alt_rank_clamped / 1000) * 100
        score = round(galaxy_score * 0.7 + alt_score * 0.3, 1)
        score = max(0.0, min(100.0, score))

        return SentimentData(
            symbol=symbol,
            score=score,
            is_bullish=score >= 60,
            is_bearish=score < 40,
            mentions=mentions,
            interactions=interactions,
            galaxy_score=galaxy_score,
            alt_rank=alt_rank,
            creators=creators,
            source="lunarcrush",
            raw_data=data,
        )

    # ── Private: Cache Management ────────────────────────

    def _get_cached(self, symbol: str) -> SentimentData | None:
        """Return cached data if fresh, else None."""
        entry = self._cache.get(symbol)
        if entry is None:
            return None
        if time.monotonic() - entry.timestamp > self.cache_ttl:
            del self._cache[symbol]
            return None
        return entry.data

    def _set_cache(self, symbol: str, data: SentimentData) -> None:
        """Store data in cache."""
        self._cache[symbol] = _CacheEntry(
            data=data,
            timestamp=time.monotonic(),
        )


class _CacheEntry:
    """Simple cache entry with timestamp."""

    __slots__ = ("data", "timestamp")

    def __init__(self, data: SentimentData, timestamp: float) -> None:
        self.data = data
        self.timestamp = timestamp


# ── Module-Level Factory ─────────────────────────────────

_global_sentiment_feed: SentimentFeed | None = None


def get_sentiment_feed() -> SentimentFeed:
    """Return cached SentimentFeed singleton.

    Uses LunarCrushFeed if API key is configured, else NullSentimentFeed.
    """
    global _global_sentiment_feed
    if _global_sentiment_feed is None:
        settings = get_settings()
        api_key = settings.lunarcrush_api_key.get_secret_value()
        if api_key:
            _global_sentiment_feed = LunarCrushFeed(
                api_key=api_key,
                cache_ttl_minutes=settings.sentiment_cache_ttl_minutes,
            )
            logger.info(
                "Sentiment feed: LunarCrush (cache TTL=%dm)",
                settings.sentiment_cache_ttl_minutes,
            )
        else:
            _global_sentiment_feed = NullSentimentFeed()
            logger.info("Sentiment feed: NullSentimentFeed (no API key)")
    return _global_sentiment_feed


def _normalize_symbol(symbol: str) -> str:
    """Strip common quote-currency suffixes for LunarCrush lookup."""
    s = symbol.upper().strip()
    for suffix in _STRIP_SUFFIXES:
        if s.endswith(suffix) and len(s) > len(suffix):
            s = s[: -len(suffix)]
            break
    return s
