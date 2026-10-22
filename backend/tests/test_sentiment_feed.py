# tests/test_sentiment_feed.py
"""Tests for Social Sentiment Feed — LunarCrush and fallback."""
from __future__ import annotations

import pytest

from app.market_data.sentiment_feed import (
    LunarCrushFeed,
    NullSentimentFeed,
    _normalize_symbol,
)
from app.market_data.sentiment_models import SentimentData


class TestSentimentDataModel:
    """Test SentimentData Pydantic model."""

    def test_neutral_factory(self) -> None:
        data = SentimentData.neutral("BTC")
        assert data.symbol == "BTC"
        assert data.score == 50.0
        assert data.is_bullish is False
        assert data.is_bearish is False
        assert data.source == "neutral"

    def test_bullish_threshold(self) -> None:
        data = SentimentData(symbol="BTC", score=65.0, is_bullish=True)
        assert data.is_bullish is True

    def test_score_clamped(self) -> None:
        data = SentimentData(symbol="BTC", score=0.0)
        assert data.score == 0.0
        data2 = SentimentData(symbol="BTC", score=100.0)
        assert data2.score == 100.0


class TestNullSentimentFeed:
    """Test NullSentimentFeed (fallback when no API key)."""

    @pytest.mark.asyncio
    async def test_returns_neutral(self) -> None:
        feed = NullSentimentFeed()
        data = await feed.get_social_metrics("BTCUSDT")
        assert data.score == 50.0
        assert data.source == "neutral"
        assert data.symbol == "BTC"  # USDT stripped


class TestLunarCrushFeed:
    """Test LunarCrushFeed without hitting real API."""

    def test_parse_response_valid(self) -> None:
        raw = {
            "data": {
                "galaxy_score": 80,
                "alt_rank": 50,
                "social_mentions": 1200,
                "social_interactions": 50000,
                "social_contributors": 350,
            },
        }
        result = LunarCrushFeed._parse_response("BTC", raw)
        assert result.symbol == "BTC"
        assert result.source == "lunarcrush"
        assert result.galaxy_score == 80.0
        assert result.alt_rank == 50
        assert result.mentions == 1200
        assert result.interactions == 50000
        assert result.creators == 350
        # Score = 80*0.7 + ((1 - 50/1000)*100)*0.3 = 56 + 28.5 = 84.5
        assert 84.0 <= result.score <= 85.0
        assert result.is_bullish is True

    def test_parse_response_low_score(self) -> None:
        raw = {
            "data": {
                "galaxy_score": 20,
                "alt_rank": 900,
                "social_mentions": 10,
                "social_interactions": 100,
                "social_contributors": 5,
            },
        }
        result = LunarCrushFeed._parse_response("DOGE", raw)
        assert result.is_bearish is True
        assert result.score < 40

    @pytest.mark.asyncio
    async def test_fallback_without_api_key(self) -> None:
        feed = LunarCrushFeed(api_key="")
        data = await feed.get_social_metrics("ETH")
        assert data.source == "neutral"
        assert data.score == 50.0

    @pytest.mark.asyncio
    async def test_cache_works(self) -> None:
        feed = LunarCrushFeed(api_key="", cache_ttl_minutes=60)
        # First call → neutral (no key)
        d1 = await feed.get_social_metrics("BTC")
        assert d1.source == "neutral"
        # Second call should use cache
        d2 = await feed.get_social_metrics("BTC")
        assert d2.source == "neutral"
        assert d1.score == d2.score

    def test_clear_cache(self) -> None:
        feed = LunarCrushFeed(api_key="")
        feed._cache["TEST"] = type(
            "_CacheEntry", (), {"data": None, "timestamp": 0},
        )()
        feed.clear_cache()
        assert len(feed._cache) == 0


class TestSymbolNormalization:
    """Test _normalize_symbol helper."""

    def test_strip_usdt(self) -> None:
        assert _normalize_symbol("BTCUSDT") == "BTC"

    def test_strip_usd(self) -> None:
        assert _normalize_symbol("ETHUSD") == "ETH"

    def test_strip_busd(self) -> None:
        assert _normalize_symbol("BNBBUSD") == "BNB"

    def test_strip_irt(self) -> None:
        assert _normalize_symbol("BTCIRT") == "BTC"

    def test_no_strip_plain(self) -> None:
        assert _normalize_symbol("BTC") == "BTC"

    def test_lowercase_normalized(self) -> None:
        assert _normalize_symbol("btcusdt") == "BTC"
