# app/strategy/feature_calculator.py
"""
Feature Calculator for YAML-driven strategies.

Computes trading features from raw candle data that are then used
by condition evaluators in strategy YAML files.  Also provides
async enrichment for AI agent verification and social sentiment.
"""
from __future__ import annotations

import logging
from typing import Any

from app.indicators.atr import get_latest_atr
from app.indicators.risk_reward import calculate_risk_reward
from app.indicators.rsi import get_latest_rsi
from app.indicators.volume import check_volume_confirmation
from app.strategy.level_detector import evaluate_location_validity
from app.strategy.momentum_filter import evaluate_15m_momentum
from app.strategy.pattern_detector import detect_1h_patterns
from app.strategy.structure_analyzer import (
    TrendDirection,
    analyze_4h_structure,
)

logger = logging.getLogger("algotrade.strategy.feature_calculator")


def compute_price_action_features(
    h4_highs: list[float],
    h4_lows: list[float],
    h4_closes: list[float],
    h1_opens: list[float],
    h1_highs: list[float],
    h1_lows: list[float],
    h1_closes: list[float],
    h1_volumes: list[float],
    m15_closes: list[float],
    m15_volumes: list[float],
    current_price: float,
) -> dict[str, Any]:
    """
    Compute standard price action features used by 8-criteria and
    pattern-based strategies.

    Returns nested dict accessible via dot-path notation.
    """
    features: dict[str, Any] = {}

    # -- Structure (4H) --
    struct = analyze_4h_structure(h4_highs, h4_lows, h4_closes)
    features["structure"] = {
        "valid": struct.direction != TrendDirection.NEUTRAL,
        "bullish": struct.direction == TrendDirection.BULLISH,
        "bearish": struct.direction == TrendDirection.BEARISH,
        "has_bos": struct.has_bos,
        "has_choch": struct.has_choch,
        "direction": struct.direction.value,
    }

    direction = "LONG" if features["structure"]["bullish"] else "SHORT"
    features["direction"] = direction

    # -- Location (S/R, OB, FVG) --
    loc = evaluate_location_validity(
        current_price, h1_highs, h1_lows, direction=direction,
    )
    features["location"] = {
        "valid": loc.is_valid_location,
        "near_support": loc.near_support,
        "near_resistance": loc.near_resistance,
        "in_fvg": loc.in_fvg,
        "in_order_block": loc.in_order_block,
    }

    # -- Pattern (1H) --
    pat = detect_1h_patterns(h1_opens, h1_highs, h1_lows, h1_closes)
    features["pattern"] = {
        "bullish": pat.is_bullish,
        "bearish": pat.is_bearish,
        "name": pat.pattern_name,
        "confirmed": (
            (direction == "LONG" and pat.is_bullish)
            or (direction == "SHORT" and pat.is_bearish)
        ),
    }

    # -- Momentum (15M) --
    mom = evaluate_15m_momentum(m15_closes, m15_volumes, direction=direction)
    features["momentum"] = {
        "confirmed": mom.is_confirmed,
        "rsi_slope_positive": mom.rsi_slope_positive,
        "volume_ok": mom.volume_ok,
    }

    # -- RSI (1H, 14-period) --
    rsi_val = get_latest_rsi(h1_closes, period=14)
    rsi_confirmed = (
        (40.0 <= rsi_val <= 70.0)
        if direction == "LONG"
        else (30.0 <= rsi_val <= 60.0)
    )
    features["rsi"] = {
        "value": round(rsi_val, 2),
        "confirmed": rsi_confirmed,
    }

    # -- Volume --
    vol_ok, vol_ratio, _ = check_volume_confirmation(
        h1_volumes, period=10, min_ratio=1.0,
    )
    features["volume"] = {
        "confirmed": vol_ok,
        "ratio": round(vol_ratio, 2),
    }

    # -- Stop Loss & Risk/Reward --
    if direction == "LONG":
        sl_ref = min(h1_lows[-5:]) if len(h1_lows) >= 5 else current_price * 0.98
        stop_loss = round(sl_ref * 0.998, 6)
        risk_dist = (current_price - stop_loss) / current_price
    else:
        sl_ref = max(h1_highs[-5:]) if len(h1_highs) >= 5 else current_price * 1.02
        stop_loss = round(sl_ref * 1.002, 6)
        risk_dist = (stop_loss - current_price) / current_price

    valid_stop = 0.001 < risk_dist < 0.08
    tp1 = (
        current_price + (current_price - stop_loss) * 1.5
        if direction == "LONG"
        else current_price - (stop_loss - current_price) * 1.5
    )
    rr = calculate_risk_reward(
        current_price, stop_loss, tp1, direction=direction,
    )
    features["risk"] = {
        "stop_loss": stop_loss,
        "stop_valid": valid_stop,
        "stop_distance_pct": round(risk_dist * 100, 3),
    }
    features["rr"] = {
        "value": round(rr, 2),
        "confirmed": rr >= 1.5,
        "tp1": round(tp1, 6),
    }

    # -- ATR --
    if len(h1_closes) >= 14:
        atr = get_latest_atr(h1_highs, h1_lows, h1_closes, period=14)
        features["atr"] = {"value": round(atr, 6), "period": 14}
    else:
        features["atr"] = {"value": current_price * 0.01, "period": 14}

    return features


def compute_wave_features(
    wave_points: dict[str, float],
    current_price: float,
    direction: str = "LONG",
) -> dict[str, Any]:
    """
    Compute corrective-pattern features from user-supplied wave points.

    Expected keys: P0, P1, P2, P3, P4 (and optionally P5).
    """
    p0 = wave_points.get("P0", 0.0)
    p1 = wave_points.get("P1", 0.0)
    p2 = wave_points.get("P2", 0.0)
    p3 = wave_points.get("P3", 0.0)
    p4 = wave_points.get("P4", 0.0)
    p5 = wave_points.get("P5", current_price)

    # Wave lengths
    i1_len = abs(p1 - p0) if p0 and p1 else 0.001
    a_len = abs(p2 - p1) if p1 and p2 else 0.001
    b_len = abs(p3 - p2) if p2 and p3 else 0.0
    c_len = abs(p4 - p3) if p3 and p4 else 0.0
    i2_len = abs(p5 - p4) if p4 and p5 else 0.0

    # Retracement depth: A / impulse1
    retr = a_len / i1_len if i1_len > 0 else 0.0

    # Ratios
    b_over_a = b_len / a_len if a_len > 0 else 0.0
    c_over_a = c_len / a_len if a_len > 0 else 0.0
    i2_ratio = i2_len / i1_len if i1_len > 0 else 0.0

    # Slope ratio (simple: i2 distance / i1 distance)
    slope_ratio = i2_len / i1_len if i1_len > 0 else 0.0

    # Direction checks
    is_bullish_i1 = p1 > p0
    i2_opposes_c = (p5 > p4) != (p4 > p3) if p4 != p3 else False

    # Completion: i2 crossed P4 level
    i2_crossed_p4 = p5 > p4 if is_bullish_i1 else p5 < p4

    # Stop loss & RR for entry B (at P4)
    entry_b = p4
    stop_b = p0  # Conservative stop at origin
    risk_b = abs(entry_b - stop_b) if entry_b != stop_b else 0.001
    target_b = entry_b + (risk_b * 1.5 if is_bullish_i1 else -risk_b * 1.5)
    rr_entry_b = abs(p5 - entry_b) / risk_b if risk_b > 0 else 0.0

    # Entry A (at P2 level)
    entry_a = p2
    stop_a = p0
    risk_a = abs(entry_a - stop_a) if entry_a != stop_a else 0.001
    rr_entry_a = abs(p5 - entry_a) / risk_a if risk_a > 0 else 0.0

    return {
        "structure_valid": i1_len > 0 and a_len > 0,
        "invalidated": False,
        "metrics": {
            "retracement": round(retr, 4),
            "wave_a_retr": round(retr, 4),
            "b_over_a": round(b_over_a, 4),
            "c_over_a": round(c_over_a, 4),
        },
        "completion": {"i2_crossed_P4": i2_crossed_p4},
        "direction": {
            "i2_opposes_C": i2_opposes_c,
            "i2_same_as_C": not i2_opposes_c,
            "bullish_impulse": is_bullish_i1,
        },
        "impulses": {
            "i1_length": round(i1_len, 6),
            "i2_length": round(i2_len, 6),
            "i2_ratio": round(i2_ratio, 4),
            "i2_slope_ratio": round(slope_ratio, 4),
        },
        "rr": {
            "by_entry": {
                "entry_a": round(rr_entry_a, 2),
                "entry_b": round(rr_entry_b, 2),
            },
        },
        "risk": {
            "stop_distance": round(risk_b, 6),
            "entry_b": round(entry_b, 6),
            "stop_b": round(stop_b, 6),
            "target_b": round(target_b, 6),
        },
    }


async def enrich_features_with_ai_sentiment(
    features: dict[str, Any],
    symbol: str,
    setup_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Enrich a features dict with AI verification and social sentiment.

    This is an async function because it calls external APIs.
    It should be called after ``compute_price_action_features`` or
    ``compute_wave_features`` when AI/sentiment conditions are needed.

    Args:
        features: Existing computed features dict (modified in-place).
        symbol: Trading pair symbol (e.g. "BTCUSDT").
        setup_data: Optional trade setup dict for AI verification.

    Returns:
        The enriched features dict (same reference as input).
    """
    from app.ai_agent.agent_core import get_ai_agent
    from app.market_data.sentiment_feed import get_sentiment_feed

    # ── AI Agent Verification ──
    agent = get_ai_agent()
    if setup_data:
        ai_result = await agent.verify_trade_setup(symbol, setup_data)
    else:
        # Build minimal setup_data from existing features
        score = _compute_score(features)
        minimal_setup = {
            "score": score,
            "direction": features.get("direction", "LONG"),
            "current_price": features.get("risk", {}).get("stop_loss", 0),
            "has_bos": features.get("structure", {}).get("has_bos", False),
            "has_fvg": features.get("location", {}).get("in_fvg", False),
            "stop_loss": features.get("risk", {}).get("stop_loss", 0),
            "take_profit_1": features.get("rr", {}).get("tp1", 0),
            "rr": features.get("rr", {}).get("value", 0),
            "rsi": features.get("rsi", {}).get("value", 50),
            "volume_confirmed": features.get("volume", {}).get(
                "confirmed", False,
            ),
        }
        ai_result = await agent.verify_trade_setup(symbol, minimal_setup)

    features["ai_agent"] = {
        "approved": ai_result.get("approved", False),
        "confidence": ai_result.get("confidence", 0),
        "sentiment": ai_result.get("sentiment", "NEUTRAL"),
        "reasoning": ai_result.get("reasoning", ""),
        "source": ai_result.get("source", "unknown"),
        "model": ai_result.get("model", "none"),
    }

    # ── Social Sentiment ──
    feed = get_sentiment_feed()
    sentiment = await feed.get_social_metrics(symbol)

    features["sentiment"] = {
        "score": sentiment.score,
        "is_bullish": sentiment.is_bullish,
        "is_bearish": sentiment.is_bearish,
        "mentions": sentiment.mentions,
        "galaxy_score": sentiment.galaxy_score,
        "alt_rank": sentiment.alt_rank,
        "source": sentiment.source,
    }

    return features


def _compute_score(features: dict[str, Any]) -> int:
    """Tally how many of the 8 criteria are confirmed in features."""
    checks = [
        features.get("structure", {}).get("valid", False),
        features.get("location", {}).get("valid", False),
        features.get("pattern", {}).get("confirmed", False),
        features.get("momentum", {}).get("confirmed", False),
        features.get("rsi", {}).get("confirmed", False),
        features.get("volume", {}).get("confirmed", False),
        features.get("rr", {}).get("confirmed", False),
        features.get("risk", {}).get("stop_valid", False),
    ]
    return sum(1 for c in checks if c)
