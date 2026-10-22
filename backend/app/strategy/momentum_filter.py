# app/strategy/momentum_filter.py
"""
15M Momentum Filter.

Rule #4: The 15M timeframe acts strictly as a final momentum filter,
NOT a standalone signal generator.

Confirms that immediate momentum aligns with the 4H trend and 1H pattern:
- RSI(14) in favorable zone (e.g. > 45 and not overbought for longs)
- Volume is active (above recent 15M average)
- Short-term directional momentum (recent closed candles show impulse)
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.indicators.rsi import get_latest_rsi
from app.indicators.volume import check_volume_confirmation


@dataclass
class MomentumResult:
    """Output of 15M momentum filter analysis."""
    is_confirmed: bool
    rsi_15m: float
    volume_ratio: float
    directional_strength: float
    description: str


def evaluate_15m_momentum(
    closes: Sequence[float],
    volumes: Sequence[float],
    direction: str = "LONG",
    rsi_period: int = 14,
    volume_ma_period: int = 10,
) -> MomentumResult:
    """
    Evaluate if 15M momentum confirms a trade in the given direction.

    For LONG:
    - RSI > 45 and RSI < 70 (healthy momentum without extreme overbought exhaustion)
    - Positive slope / recent price movement
    - Volume is not dry
    """
    if len(closes) < max(rsi_period + 2, volume_ma_period):
        return MomentumResult(
            is_confirmed=False,
            rsi_15m=50.0,
            volume_ratio=1.0,
            directional_strength=0.0,
            description="داده‌های ۱۵ دقیقه برای بررسی فیلتر مومنتوم ناکافی است.",
        )

    rsi = get_latest_rsi(closes, rsi_period)
    is_vol_confirmed, curr_vol, vol_ma = check_volume_confirmation(
        volumes, period=volume_ma_period, min_ratio=0.85
    )
    vol_ratio = (curr_vol / vol_ma) if vol_ma > 0 else 1.0

    # Directional momentum over last 3 closed candles
    recent_delta = closes[-1] - closes[-3]
    directional_strength = (recent_delta / closes[-3]) * 100.0 if closes[-3] > 0 else 0.0

    if direction.upper() == "LONG":
        rsi_ok = 42.0 <= rsi <= 72.0
        dir_ok = directional_strength >= -0.1  # Not plunging downward
        vol_ok = vol_ratio >= 0.8
        is_confirmed = rsi_ok and dir_ok and vol_ok
        desc = (
            f"مومنتوم ۱۵ دقیقه صعودی تأیید شد (RSI={rsi:.1f}, VolRatio={vol_ratio:.2f})"
            if is_confirmed
            else f"مومنتوم ۱۵ دقیقه کافی نیست (RSI={rsi:.1f}, VolRatio={vol_ratio:.2f})"
        )
    else:  # SHORT
        rsi_ok = 28.0 <= rsi <= 58.0
        dir_ok = directional_strength <= 0.1
        vol_ok = vol_ratio >= 0.8
        is_confirmed = rsi_ok and dir_ok and vol_ok
        desc = (
            f"مومنتوم ۱۵ دقیقه نزولی تأیید شد (RSI={rsi:.1f}, VolRatio={vol_ratio:.2f})"
            if is_confirmed
            else f"مومنتوم ۱۵ دقیقه کافی نیست (RSI={rsi:.1f}, VolRatio={vol_ratio:.2f})"
        )

    return MomentumResult(
        is_confirmed=is_confirmed,
        rsi_15m=rsi,
        volume_ratio=vol_ratio,
        directional_strength=directional_strength,
        description=desc,
    )
