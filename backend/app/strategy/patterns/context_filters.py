# app/strategy/patterns/context_filters.py
"""
Toggleable Context Filters for Pattern Quality Assessment.

These filters NEVER delete patterns. They only TAG each pattern with
contextual information (trend alignment, structure breaks, volume
behavior, RSI divergence) so the UI can highlight strong setups and
grey-out weaker ones.

Each filter can be independently enabled/disabled from the frontend,
allowing the trader to gradually tighten or loosen their criteria.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger("algotrade.strategy.context_filters")


@dataclass
class FilterConfig:
    """
    Configuration for optional context filters.

    All filters default to False (disabled). The frontend sends the
    user's toggle state, and the backend applies matching tags.
    """

    choch_bos_enabled: bool = False
    volume_enabled: bool = False
    rsi_divergence_enabled: bool = False
    trend_alignment_enabled: bool = False


@dataclass
class ContextTag:
    """A single contextual tag attached to a pattern."""

    key: str
    label_fa: str
    label_en: str
    passed: bool  # Did the pattern satisfy this context check?
    value: str = ""  # Diagnostic display value

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label_fa,
            "label_en": self.label_en,
            "passed": self.passed,
            "value": self.value,
        }


def apply_context_filters(
    marker: dict[str, Any],
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    volumes: np.ndarray | None,
    filter_config: FilterConfig,
) -> list[ContextTag]:
    """
    Evaluate all enabled context filters and return tags.

    IMPORTANT: This function NEVER removes or rejects a pattern.
    It only produces tags that the UI can use for visual emphasis.

    Args:
        marker: The pattern marker dict (contains p0_idx, p4_idx, direction).
        highs/lows/closes: Full candle arrays.
        volumes: Volume array (may be None if exchange doesn't provide it).
        filter_config: Which filters are enabled by the user.

    Returns:
        List of ContextTag objects (one per enabled filter).
    """
    tags: list[ContextTag] = []

    p0_idx = marker.get("p0_idx", 0)
    p1_idx = marker.get("points", [{}])[1].get("time", 0)  # fallback
    p4_idx = marker.get("p4_idx", 0)
    is_bull = marker.get("direction") == "bullish"

    # Use indices from cycle data embedded in marker
    cycle_p1_idx = _find_p1_idx(marker)

    if filter_config.choch_bos_enabled:
        tags.append(
            _check_structure_break(highs, lows, closes, p0_idx, is_bull)
        )

    if filter_config.trend_alignment_enabled:
        tags.append(
            _check_trend_alignment(highs, lows, closes, p0_idx, is_bull)
        )

    if filter_config.volume_enabled and volumes is not None:
        tags.append(
            _check_volume_dry_up(
                volumes, cycle_p1_idx, p4_idx, is_bull,
            )
        )

    if filter_config.rsi_divergence_enabled:
        tags.append(
            _check_rsi_context(closes, p4_idx, is_bull)
        )

    return tags


def _find_p1_idx(marker: dict[str, Any]) -> int:
    """Extract P1 index from marker points."""
    points = marker.get("points", [])
    if len(points) >= 2:
        # P1 is the second point
        p1_time = points[1].get("time", 0)
        # We can't directly get index from time, use p0_idx as fallback
        p0_idx = marker.get("p0_idx", 0)
        p4_idx = marker.get("p4_idx", 0)
        # Estimate P1 as roughly 1/3 into the pattern
        return p0_idx + max(1, (p4_idx - p0_idx) // 3)
    return marker.get("p0_idx", 0) + 3


# ─────────────────────────────────────────────────
# Individual filter implementations
# ─────────────────────────────────────────────────

def _check_structure_break(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    p0_idx: int,
    is_bull: bool,
) -> ContextTag:
    """
    Check if the impulse starting at P0 is associated with a BOS or CHoCH.

    Looks at the swing structure BEFORE P0 to determine if the impulse
    is a trend continuation (BOS) or a reversal (CHoCH).
    """
    from app.strategy.structure_analyzer import find_swing_points

    # Analyze structure using candles up to P0
    lookback_end = min(p0_idx + 1, len(highs))
    if lookback_end < 10:
        return ContextTag(
            key="choch_bos",
            label_fa="شکست ساختار (BOS/CHoCH)",
            label_en="Structure Break (BOS/CHoCH)",
            passed=False,
            value="داده ناکافی",
        )

    swings = find_swing_points(
        highs[:lookback_end], lows[:lookback_end], lookback=3,
    )
    high_swings = [s for s in swings if s.is_high]
    low_swings = [s for s in swings if not s.is_high]

    if len(high_swings) < 2 or len(low_swings) < 2:
        return ContextTag(
            key="choch_bos",
            label_fa="شکست ساختار (BOS/CHoCH)",
            label_en="Structure Break (BOS/CHoCH)",
            passed=False,
            value="سوئینگ ناکافی",
        )

    curr_high = high_swings[-1].price
    prev_high = high_swings[-2].price
    curr_low = low_swings[-1].price
    prev_low = low_swings[-2].price

    is_hh = curr_high > prev_high
    is_hl = curr_low > prev_low
    is_ll = curr_low < prev_low

    if is_bull:
        # Bullish impulse: look for HH+HL (BOS) or CHoCH (break above high in downtrend)
        has_bos = is_hh and is_hl
        has_choch = not has_bos and is_hh
        passed = has_bos or has_choch
        label = "BOS صعودی" if has_bos else "CHoCH صعودی" if has_choch else "بدون شکست"
    else:
        # Bearish impulse
        has_bos = not is_hh and is_ll
        has_choch = not has_bos and is_ll
        passed = has_bos or has_choch
        label = "BOS نزولی" if has_bos else "CHoCH نزولی" if has_choch else "بدون شکست"

    return ContextTag(
        key="choch_bos",
        label_fa="شکست ساختار (BOS/CHoCH)",
        label_en="Structure Break (BOS/CHoCH)",
        passed=passed,
        value=label,
    )


def _check_trend_alignment(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    p0_idx: int,
    is_bull: bool,
) -> ContextTag:
    """
    Check if the impulse direction aligns with the broader trend.

    Uses a simple 50-period EMA slope as trend proxy.
    """
    lookback_end = min(p0_idx + 1, len(closes))
    if lookback_end < 20:
        return ContextTag(
            key="trend_aligned",
            label_fa="همسویی با روند",
            label_en="Trend Alignment",
            passed=False,
            value="داده ناکافی",
        )

    # Simple trend check: compare last 20 closes avg vs last 50 closes avg
    period = min(50, lookback_end)
    short_period = min(20, lookback_end)
    long_avg = float(np.mean(closes[lookback_end - period:lookback_end]))
    short_avg = float(np.mean(closes[lookback_end - short_period:lookback_end]))

    if is_bull:
        aligned = short_avg > long_avg
        trend_label = "صعودی ✅" if aligned else "خلاف روند ⚠️"
    else:
        aligned = short_avg < long_avg
        trend_label = "نزولی ✅" if aligned else "خلاف روند ⚠️"

    return ContextTag(
        key="trend_aligned",
        label_fa="همسویی با روند",
        label_en="Trend Alignment",
        passed=aligned,
        value=trend_label,
    )


def _check_volume_dry_up(
    volumes: np.ndarray,
    p1_idx: int,
    p4_idx: int,
    is_bull: bool,
) -> ContextTag:
    """
    Check if volume dried up during the correction (P1 → P4).

    A healthy correction should show DECLINING volume as the correction
    progresses, indicating lack of conviction in the counter-move.
    The breakout candle should ideally show a volume spike.
    """
    if p1_idx >= p4_idx or p4_idx >= len(volumes) or p1_idx < 0:
        return ContextTag(
            key="volume_dry_up",
            label_fa="خشک شدن حجم در اصلاح",
            label_en="Volume Dry-Up in Correction",
            passed=False,
            value="داده ناکافی",
        )

    correction_vols = volumes[p1_idx:p4_idx + 1]
    if len(correction_vols) < 3:
        return ContextTag(
            key="volume_dry_up",
            label_fa="خشک شدن حجم در اصلاح",
            label_en="Volume Dry-Up in Correction",
            passed=False,
            value="کندل ناکافی",
        )

    # Compare first half vs second half of correction volume
    mid = len(correction_vols) // 2
    first_half_avg = float(np.mean(correction_vols[:mid])) if mid > 0 else 1.0
    second_half_avg = float(np.mean(correction_vols[mid:])) if mid > 0 else 1.0

    # Volume should decrease: second half should be lower than first half
    dry_up = first_half_avg > 0 and second_half_avg < first_half_avg * 0.85
    ratio = second_half_avg / first_half_avg if first_half_avg > 0 else 1.0

    return ContextTag(
        key="volume_dry_up",
        label_fa="خشک شدن حجم در اصلاح",
        label_en="Volume Dry-Up in Correction",
        passed=dry_up,
        value=f"نسبت: {ratio:.2f}" if dry_up else f"حجم ثابت ({ratio:.2f})",
    )


def _check_rsi_context(
    closes: np.ndarray,
    p4_idx: int,
    is_bull: bool,
) -> ContextTag:
    """
    Check RSI context at the pattern completion point (P4).

    For bullish patterns: RSI near oversold (<40) is confirming.
    For bearish patterns: RSI near overbought (>60) is confirming.
    """
    if p4_idx < 14 or p4_idx >= len(closes):
        return ContextTag(
            key="rsi_context",
            label_fa="RSI در ناحیه مناسب",
            label_en="RSI Context",
            passed=False,
            value="داده ناکافی",
        )

    # Calculate RSI(14)
    rsi_data = closes[max(0, p4_idx - 100):p4_idx + 1]
    rsi = _calc_rsi(rsi_data, period=14)

    if rsi is None:
        return ContextTag(
            key="rsi_context",
            label_fa="RSI در ناحیه مناسب",
            label_en="RSI Context",
            passed=False,
            value="محاسبه ناموفق",
        )

    if is_bull:
        passed = rsi < 45  # Oversold-ish area for bullish entry
        label = f"RSI={rsi:.0f} (اشباع فروش ✅)" if passed else f"RSI={rsi:.0f}"
    else:
        passed = rsi > 55  # Overbought-ish area for bearish entry
        label = f"RSI={rsi:.0f} (اشباع خرید ✅)" if passed else f"RSI={rsi:.0f}"

    return ContextTag(
        key="rsi_context",
        label_fa="RSI در ناحیه مناسب",
        label_en="RSI Context",
        passed=passed,
        value=label,
    )


def _calc_rsi(closes: np.ndarray, period: int = 14) -> float | None:
    """Calculate RSI for the last value in the array."""
    if len(closes) < period + 1:
        return None
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = float(np.mean(gains[-period:]))
    avg_loss = float(np.mean(losses[-period:]))

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))
