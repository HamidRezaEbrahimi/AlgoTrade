# app/strategy/pattern_detector.py
"""
1H Entry Pattern Detector & Historical Pattern Scanner.

Identifies classic Price Action candlestick patterns on closed candles:
1. Bullish / Bearish Engulfing
2. Bullish / Bearish Pin Bar (Shooting Star / Hammer)
3. Morning Star / Evening Star
4. Historical candle series pattern scanning for chart overlay markers.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.models.candle import Candle

logger = logging.getLogger("algotrade.strategy.pattern_detector")


class PatternType(StrEnum):
    BULLISH_ENGULFING = "BULLISH_ENGULFING"
    BEARISH_ENGULFING = "BEARISH_ENGULFING"
    PIN_BAR_BULLISH = "PIN_BAR_BULLISH"
    PIN_BAR_BEARISH = "PIN_BAR_BEARISH"
    HAMMER = "HAMMER"
    SHOOTING_STAR = "SHOOTING_STAR"
    MORNING_STAR = "MORNING_STAR"
    EVENING_STAR = "EVENING_STAR"
    NONE = "NONE"


@dataclass
class PatternResult:
    """Detection result for candlestick pattern."""
    pattern_type: PatternType
    is_bullish: bool
    is_bearish: bool
    confidence: float
    description: str


def detect_bullish_engulfing(
    opens: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
) -> bool:
    if len(closes) < 2:
        return False
    prev_o, prev_c = opens[-2], closes[-2]
    curr_o, curr_c = opens[-1], closes[-1]
    if not (prev_c < prev_o and curr_c > curr_o):
        return False
    return curr_c >= prev_o and curr_o <= (prev_c * 1.005)


def detect_bearish_engulfing(
    opens: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
) -> bool:
    if len(closes) < 2:
        return False
    prev_o, prev_c = opens[-2], closes[-2]
    curr_o, curr_c = opens[-1], closes[-1]
    if not (prev_c > prev_o and curr_c < curr_o):
        return False
    return curr_c <= prev_o and curr_o >= (prev_c * 0.995)


def detect_bullish_pin_bar(
    opens: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    wick_ratio: float = 2.0,
) -> bool:
    if len(closes) < 1:
        return False
    o, h, low_val, c = opens[-1], highs[-1], lows[-1], closes[-1]
    body = abs(c - o)
    total_range = h - low_val
    if total_range <= 0.0 or body == 0.0:
        return False
    lower_wick = min(o, c) - low_val
    upper_wick = h - max(o, c)
    return (lower_wick >= body * wick_ratio) and (upper_wick <= body * 1.5)


def detect_bearish_pin_bar(
    opens: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    wick_ratio: float = 2.0,
) -> bool:
    if len(closes) < 1:
        return False
    o, h, low_val, c = opens[-1], highs[-1], lows[-1], closes[-1]
    body = abs(c - o)
    total_range = h - low_val
    if total_range <= 0.0 or body == 0.0:
        return False
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - low_val
    return (upper_wick >= body * wick_ratio) and (lower_wick <= body * 1.5)


def detect_hammer(
    opens: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
) -> bool:
    if len(closes) < 1:
        return False
    o, h, low_val, c = opens[-1], highs[-1], lows[-1], closes[-1]
    body = abs(c - o)
    lower_wick = min(o, c) - low_val
    upper_wick = h - max(o, c)
    return (lower_wick >= 2.0 * body) and (upper_wick <= 0.3 * body) and (body > 0.0)


def detect_morning_star(
    opens: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
) -> bool:
    if len(closes) < 3:
        return False
    o1, c1 = opens[-3], closes[-3]
    o2, c2 = opens[-2], closes[-2]
    o3, c3 = opens[-1], closes[-1]
    is_c1_bearish = c1 < o1
    c1_body = o1 - c1
    c2_body = abs(c2 - o2)
    is_c2_star = c2_body < (c1_body * 0.5)
    is_c3_bullish = c3 > o3
    is_c3_strong = c3 > (c1 + c1_body * 0.5)
    return is_c1_bearish and is_c2_star and is_c3_bullish and is_c3_strong


def detect_1h_patterns(
    opens: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
) -> PatternResult:
    """Check for all supported 1H entry patterns in prioritized order."""
    if detect_morning_star(opens, highs, lows, closes):
        return PatternResult(
            pattern_type=PatternType.MORNING_STAR,
            is_bullish=True,
            is_bearish=False,
            confidence=0.90,
            description="الگوی ستاره صبحگاهی (Morning Star) شناسایی شد.",
        )
    if detect_bullish_engulfing(opens, highs, lows, closes):
        return PatternResult(
            pattern_type=PatternType.BULLISH_ENGULFING,
            is_bullish=True,
            is_bearish=False,
            confidence=0.85,
            description="الگوی پوشای صعودی (Bullish Engulfing) شناسایی شد.",
        )
    if detect_bearish_engulfing(opens, highs, lows, closes):
        return PatternResult(
            pattern_type=PatternType.BEARISH_ENGULFING,
            is_bullish=False,
            is_bearish=True,
            confidence=0.85,
            description="الگوی پوشای نزولی (Bearish Engulfing) شناسایی شد.",
        )
    if detect_bullish_pin_bar(opens, highs, lows, closes) or detect_hammer(opens, highs, lows, closes):
        return PatternResult(
            pattern_type=PatternType.PIN_BAR_BULLISH,
            is_bullish=True,
            is_bearish=False,
            confidence=0.80,
            description="الگوی پین‌بار/چکش صعودی (Bullish Pin Bar) شناسایی شد.",
        )
    if detect_bearish_pin_bar(opens, highs, lows, closes):
        return PatternResult(
            pattern_type=PatternType.PIN_BAR_BEARISH,
            is_bullish=False,
            is_bearish=True,
            confidence=0.80,
            description="الگوی پین‌بار نزولی (Bearish Pin Bar) شناسایی شد.",
        )

    return PatternResult(
        pattern_type=PatternType.NONE,
        is_bullish=False,
        is_bearish=False,
        confidence=0.0,
        description="الگوی کندلی معتبری در تایم‌فریم ۱ ساعته یافت نشد.",
    )


def scan_series_patterns(
    candles: Sequence[Candle],
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Pure AlefTrade Pattern Engine.

    All legacy candlestick, flag, and uncalibrated wave patterns are eliminated.
    Only high-precision Elliott Wave patterns and Developing Wave PRZ from AlefTrade
    are scanned and returned.
    """
    if len(candles) < 20:
        return []

    try:
        from app.strategy.alef_adapter import scan_patterns_with_alef

        return scan_patterns_with_alef(
            candles,
            symbol=symbol,
            timeframe=timeframe,
            config=config,
        )
    except Exception:
        logger.exception("AlefTrade pattern scan failed — continuing with empty list")
        return []


def _apply_context_tags(
    wave_markers: list[dict[str, Any]],
    candles: Sequence[Candle],
    config: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Apply toggleable context filters to wave markers (tag-only, no rejection)."""
    try:
        import numpy as np
        from app.strategy.patterns.context_filters import (
            FilterConfig,
            apply_context_filters,
        )

        # Build filter config from request config
        filters_cfg = (config or {}).get("context_filters", {})
        filter_config = FilterConfig(
            choch_bos_enabled=bool(filters_cfg.get("choch_bos", False)),
            volume_enabled=bool(filters_cfg.get("volume", False)),
            rsi_divergence_enabled=bool(filters_cfg.get("rsi", False)),
            trend_alignment_enabled=bool(filters_cfg.get("trend", False)),
        )

        # Skip if no filters are enabled
        if not any([
            filter_config.choch_bos_enabled,
            filter_config.volume_enabled,
            filter_config.rsi_divergence_enabled,
            filter_config.trend_alignment_enabled,
        ]):
            return wave_markers

        highs = np.array([float(c.high) for c in candles], dtype=float)
        lows = np.array([float(c.low) for c in candles], dtype=float)
        closes = np.array([float(c.close) for c in candles], dtype=float)
        volumes = None
        if hasattr(candles[0], "volume") and candles[0].volume is not None:
            volumes = np.array([float(c.volume) for c in candles], dtype=float)

        for marker in wave_markers:
            tags = apply_context_filters(
                marker, highs, lows, closes, volumes, filter_config,
            )
            marker["context_tags"] = [t.to_dict() for t in tags]

    except Exception:
        logger.exception("Context filter application failed — tags omitted")

    return wave_markers

