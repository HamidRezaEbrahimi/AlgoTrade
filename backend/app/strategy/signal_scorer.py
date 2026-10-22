# app/strategy/signal_scorer.py
"""
8-Criteria Signal Scorer.

Core logic orchestrating all strategy components:
Entry requires minimum 6 out of 8 confirmations:
1. Proper structure (4H HH/HL, BOS, CHoCH)
2. Valid location (S/R, Order Block, FVG)
3. Entry pattern confirmation (1H Engulfing, Pin Bar, Hammer, Morning Star)
4. Momentum confirmation (15M)
5. RSI(14) confirmation
6. Volume > MA(10) confirmation
7. Risk/Reward >= 1.5
8. Valid Stop Loss placement
"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.indicators.risk_reward import calculate_risk_reward, calculate_target_by_rr
from app.indicators.rsi import get_latest_rsi
from app.indicators.volume import check_volume_confirmation
from app.models.signal import EntryScores, Signal
from app.strategy.level_detector import evaluate_location_validity
from app.strategy.momentum_filter import evaluate_15m_momentum
from app.strategy.pattern_detector import detect_1h_patterns
from app.strategy.structure_analyzer import TrendDirection, analyze_4h_structure

# Reason code dictionary with Persian explanations
REASONS_FA: dict[str, str] = {
    "SIGNAL_CONFIRMED_LONG": "سیگنال خرید معتبر با تأیید حداقل ۶ معیار از ۸ معیار سیستم.",
    "SIGNAL_CONFIRMED_SHORT": "سیگنال فروش معتبر با تأیید حداقل ۶ معیار از ۸ معیار سیستم.",
    "REJECTED_LOW_SCORE": "سیگنال رد شد: امتیاز کل کمتر از حداقل مجاز (۶ از ۸) است.",
    "REJECTED_UNFAVORABLE_STRUCTURE": "سیگنال رد شد: ساختار بازار ۴ ساعته نامناسب یا متناقض است.",
    "REJECTED_NO_PATTERN": "سیگنال رد شد: الگوی کندلی معتبری در تایم‌فریم ۱ ساعته شکل نگرفته است.",
    "REJECTED_POOR_RR": "سیگنال رد شد: نسبت ریسک به ریوارد کمتر از ۱:۱.۵ است.",
    "REJECTED_INVALID_STOP": "سیگنال رد شد: فاصله حد ضرر نامعتبر یا غیرمنطقی است.",
}


@dataclass
class MultiTimeframeCandles:
    """Container for multi-timeframe closed candle arrays."""
    # 4H data
    h4_highs: Sequence[float]
    h4_lows: Sequence[float]
    h4_closes: Sequence[float]
    # 1H data
    h1_opens: Sequence[float]
    h1_highs: Sequence[float]
    h1_lows: Sequence[float]
    h1_closes: Sequence[float]
    h1_volumes: Sequence[float]
    # 15M data
    m15_closes: Sequence[float]
    m15_volumes: Sequence[float]


def evaluate_signal(
    symbol: str,
    data: MultiTimeframeCandles,
    current_price: float,
    min_score: int = 6,
    min_rr: float = 1.5,
) -> Signal | None:
    """
    Evaluate all 8 criteria across 4H, 1H, and 15M closed candles.
    Returns a Signal object if score >= 6/8 and RR >= 1.5, otherwise None.
    """
    # 1. Structure Analysis (4H)
    struct_res = analyze_4h_structure(data.h4_highs, data.h4_lows, data.h4_closes)
    is_bullish_struct = struct_res.direction == TrendDirection.BULLISH or struct_res.has_choch
    is_bearish_struct = struct_res.direction == TrendDirection.BEARISH

    if not (is_bullish_struct or is_bearish_struct):
        return None  # Neutral market, skip

    direction = "LONG" if is_bullish_struct else "SHORT"

    # 2. Location (S/R, OB, FVG)
    loc_res = evaluate_location_validity(
        current_price, data.h1_highs, data.h1_lows, direction=direction
    )

    # 3. Entry Pattern (1H)
    pat_res = detect_1h_patterns(
        data.h1_opens, data.h1_highs, data.h1_lows, data.h1_closes
    )
    pattern_confirmed = (
        (direction == "LONG" and pat_res.is_bullish)
        or (direction == "SHORT" and pat_res.is_bearish)
    )

    # 4. Momentum Filter (15M)
    mom_res = evaluate_15m_momentum(
        data.m15_closes, data.m15_volumes, direction=direction
    )

    # 5. RSI(14) on 1H
    rsi_1h = get_latest_rsi(data.h1_closes, period=14)
    rsi_confirmed = (40.0 <= rsi_1h <= 70.0) if direction == "LONG" else (30.0 <= rsi_1h <= 60.0)

    # 6. Volume > MA(10) on 1H
    vol_confirmed, _, _ = check_volume_confirmation(data.h1_volumes, period=10, min_ratio=1.0)

    # Calculate Stop Loss based on recent 1H swing / structure
    if direction == "LONG":
        recent_low = min(data.h1_lows[-5:]) if len(data.h1_lows) >= 5 else current_price * 0.98
        stop_loss = round(recent_low * 0.998, 6)
        valid_stop = 0.001 < ((current_price - stop_loss) / current_price) < 0.08
    else:
        recent_high = max(data.h1_highs[-5:]) if len(data.h1_highs) >= 5 else current_price * 1.02
        stop_loss = round(recent_high * 1.002, 6)
        valid_stop = 0.001 < ((stop_loss - current_price) / current_price) < 0.08

    # 7. Targets & Risk/Reward
    tp1 = calculate_target_by_rr(current_price, stop_loss, target_rr=1.5, direction=direction)
    tp2 = calculate_target_by_rr(current_price, stop_loss, target_rr=2.5, direction=direction)
    rr_calc = calculate_risk_reward(current_price, stop_loss, tp1, direction=direction)
    rr_confirmed = rr_calc >= min_rr

    # Build 8-criteria scores
    scores = EntryScores(
        structure=is_bullish_struct if direction == "LONG" else is_bearish_struct,
        location=loc_res.is_valid_location,
        pattern=pattern_confirmed,
        momentum=mom_res.is_confirmed,
        rsi=rsi_confirmed,
        volume=vol_confirmed,
        risk_reward=rr_confirmed,
        stop_valid=valid_stop,
    )

    if scores.total < min_score or not rr_confirmed or not valid_stop:
        return None

    reason_code = "SIGNAL_CONFIRMED_LONG" if direction == "LONG" else "SIGNAL_CONFIRMED_SHORT"
    reason_fa = REASONS_FA.get(reason_code, "")

    return Signal(
        id=uuid.uuid4(),
        symbol=symbol,
        direction=direction,
        timestamp=datetime.now(UTC),
        scores=scores,
        entry_price=Decimal(str(round(current_price, 6))),
        stop_loss=Decimal(str(round(stop_loss, 6))),
        take_profit_1=Decimal(str(round(tp1, 6))),
        take_profit_2=Decimal(str(round(tp2, 6))),
        risk_reward_ratio=Decimal(str(round(rr_calc, 2))),
        reason_code=reason_code,
        reason_description=reason_fa,
        is_executed=False,
    )
