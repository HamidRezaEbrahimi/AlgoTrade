# app/strategy/patterns/wave_classifier.py
"""
Wave & Chart Pattern Classification Orchestrator (v2).

Detection Philosophy:
  1. DETECT purely by geometry: find strong impulses + A-B-C corrections.
  2. CLASSIFY via YAML pattern rules (Flag, Flat variants, etc.).
  3. CALCULATE per-pattern trade zones (Entry A/B, SL, TP1, TP2).
  4. TAG with optional context filters (CHoCH, Volume, RSI) — never reject.

No structural pre-filters (CHoCH/BOS) gate detection. All patterns are
found first, then context filters are applied as optional quality tags.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import numpy as np

from app.models.candle import Candle
from app.strategy.patterns.rule_engine import (
    PATTERN_COLORS,
    RuleEngine,
    get_detector_config,
    resolve_impulse_min_pct,
)
from app.strategy.patterns.trade_zones import calculate_trade_zones
from app.strategy.patterns.wave_points import (
    _is_local_extreme,
    build_features,
    calc_atr,
    extract_candidate_wave_cycles,
    is_clean_impulse,
)

logger = logging.getLogger("algotrade.strategy.wave_classifier")

# Kept for backward compatibility with legacy imports.
DEFAULT_DETECTOR_CONFIG = get_detector_config()


def scan_canonical_wave_patterns(
    candles: Sequence[Candle],
    config: dict[str, Any] | None = None,
    asset_class: str | None = None,
) -> list[dict[str, Any]]:
    """
    Scan candles for non-overlapping canonical wave patterns, classified
    purely by YAML rules.

    Args:
        candles: Closed candles (chronological).
        config: Per-call detector config overrides (min_impulse_atr, ...).
            May also carry ``asset_class``.
        asset_class: Asset class key for impulse-min-pct resolution
            (crypto / forex / metal / index). Overrides config value.
    """
    if len(candles) < 25:
        return []

    detector_cfg = {**get_detector_config(), **(config or {})}
    effective_class = asset_class or (config or {}).get("asset_class")
    impulse_min_pct = resolve_impulse_min_pct(detector_cfg, effective_class)

    highs = np.array([float(c.high) for c in candles], dtype=float)
    lows = np.array([float(c.low) for c in candles], dtype=float)
    closes = np.array([float(c.close) for c in candles], dtype=float)
    timestamps = [int(c.timestamp.timestamp()) for c in candles]
    n = len(candles)

    atr = calc_atr(highs, lows, closes, period=14)
    detector_cfg["_atr"] = atr  # Pass ATR to _build_marker for trade zones
    engine = RuleEngine()

    markers: list[dict[str, Any]] = []
    for direction in ("bullish", "bearish"):
        markers.extend(
            _scan_direction(
                highs, lows, closes, timestamps, n, atr, detector_cfg,
                impulse_min_pct, direction, engine,
            )
        )

    return _dedupe_overlaps(markers)


def _scan_direction(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    timestamps: list[int],
    n: int,
    atr: float,
    detector_cfg: dict[str, Any],
    impulse_min_pct: float,
    direction: str,
    engine: RuleEngine,
) -> list[dict[str, Any]]:
    """Scan one direction for wave cycles and classify them via YAML rules."""
    is_bull = direction == "bullish"
    ext_arr = lows if is_bull else highs      # impulse start anchor
    opp_arr = highs if is_bull else lows      # impulse end anchor
    want_max_start = not is_bull
    want_max_pulse = is_bull
    min_imp_atr = float(detector_cfg.get("min_impulse_atr", 1.5))

    from app.strategy.structure_analyzer import find_swing_points
    swings_3 = find_swing_points(highs, lows, lookback=3)
    swings = find_swing_points(highs, lows, lookback=2) if not swings_3 else swings_3
    
    valid_p0_indices = [s.index for s in swings if s.is_high == want_max_start and s.index < n - 8]
    valid_p1_indices = [s.index for s in swings if s.is_high == want_max_pulse]

    candidates: list[dict[str, Any]] = []
    for i in valid_p0_indices:
        valid_p1s = [idx for idx in valid_p1_indices if i < idx <= min(n - 4, i + 35)]
        for j in valid_p1s:
            p0_price = float(ext_arr[i])
            p1_price = float(opp_arr[j])

            # Pure geometry gate: impulse must be real and significant
            disp = (p1_price - p0_price) if is_bull else (p0_price - p1_price)
            if disp <= 0 or disp < min_imp_atr * atr or disp < p0_price * impulse_min_pct:
                continue

            # Impulse cleanliness check (no deep counter-moves inside the leg)
            impulse_atr = calc_atr(highs[i:j + 1], lows[i:j + 1], closes[i:j + 1])
            if not is_clean_impulse(highs, lows, i, j, impulse_atr, direction):
                continue

            for cycle in extract_candidate_wave_cycles(highs, lows, timestamps, n, i, j, direction):
                features = build_features(cycle, atr, detector_cfg, impulse_min_pct)
                pattern_def, evaluations = engine.classify(features, direction)
                if pattern_def is None:
                    continue

                candidates.append(
                    _build_marker(cycle, pattern_def, evaluations, detector_cfg, timestamps)
                )
    return candidates



def _build_marker(
    cycle: dict[str, Any],
    pattern_def: dict[str, Any],
    evaluations: list[Any],
    detector_cfg: dict[str, Any],
    timestamps: list[int],
) -> dict[str, Any]:
    """Build a chart marker dict with per-pattern trade zones."""
    is_bull = cycle["direction"] == "bullish"
    suffix = "bull" if is_bull else "bear"
    cat = str(pattern_def.get("category", "flat"))
    name_en = str(pattern_def.get("name_en", "Unknown Pattern"))
    name_fa = str(pattern_def.get("name_fa", name_en))

    p0_price = cycle["p0_price"]
    p4_price = cycle["p4_price"]
    disp = cycle["disp"]
    retrace_total = cycle["retrace_total"]
    atr = float(detector_cfg.get("_atr", 1.0))

    pts = [
        {"label": f"P0 (شروع ایمپالس ۱: {p0_price:,.0f}) {'↗' if is_bull else '↘'}", "time": timestamps[cycle["p0_idx"]], "price": p0_price},
        {"label": f"P1 ({'قله' if is_bull else 'کف'} ایمپالس ۱ / شروع A: {cycle['p1_price']:,.0f}) {'↘' if is_bull else '↗'}", "time": timestamps[cycle["p1_idx"]], "price": cycle["p1_price"]},
        {"label": f"P2 (موج A: {cycle['p2_price']:,.0f}) {'↗' if is_bull else '↘'}", "time": timestamps[cycle["p2_idx"]], "price": cycle["p2_price"]},
        {"label": f"P3 (موج B: {cycle['p3_price']:,.0f}) {'↘' if is_bull else '↗'}", "time": timestamps[cycle["p3_idx"]], "price": cycle["p3_price"]},
        {"label": f"P4 (ورود {name_en}: {p4_price:,.0f}) 🎯", "time": timestamps[cycle["p4_idx"]], "price": p4_price},
        cycle["p5_dict"],
    ]

    # Per-pattern trade zone calculation
    zones = calculate_trade_zones(cycle, cat, atr)

    if is_bull:
        color = "#22c55e" if cat == "flag" else "#3b82f6" if cat == "flat" else "#06b6d4" if cat == "wedge" else "#10b981"
    else:
        color = "#ef4444" if cat == "flag" else "#f97316" if cat == "flat" else "#d946ef" if cat == "wedge" else "#f43f5e"

    # Compute risk/reward from the new zones
    risk = abs(zones.entry_b.price - zones.stop_loss.price)
    reward = abs(zones.tp1.price - zones.entry_b.price)
    rr_ratio = round(reward / risk, 2) if risk > 0 else 1.5

    return {
        "id": f"{cat}-{cycle['p4_idx']}-{suffix}",
        "time": timestamps[cycle["p4_idx"]],
        "type": name_en.upper().replace(" ", "_"),
        "name": name_fa,
        "name_en": name_en,
        "category": cat,
        "direction": cycle["direction"],
        "price": p4_price,
        "confidence": 0.94,
        "position": "belowBar" if is_bull else "aboveBar",
        "color": "#10b981" if is_bull else "#ef4444",
        "pattern_color": color,
        "shape": "arrowUp" if is_bull else "arrowDown",
        "text": name_fa,
        "points": pts,
        "p0_idx": cycle["p0_idx"],
        "p4_idx": cycle["p4_idx"],
        "disp": disp,
        "metrics": {
            "impulse_disp": disp,
            "retrace_pct": retrace_total,
            "b_over_a": round(cycle["b_amp"] / cycle["a_amp"], 2) if cycle["a_amp"] > 0 else 0.0,
            "c_over_a": round(cycle["c_amp"] / cycle["a_amp"], 2) if cycle["a_amp"] > 0 else 0.0,
        },
        "rules_evaluation": [e.to_dict() for e in evaluations],
        "quality": disp * (1.0 - abs(0.382 - retrace_total)),
        # New: per-pattern trade zones
        "trade_zones": zones.to_dict(),
        # Context tags populated by pattern_detector after full scan
        "context_tags": [],
        # Legacy trade_setup (backward compatible)
        "trade_setup": {
            "entry": zones.entry_b.price,
            "stop_loss": zones.stop_loss.price,
            "take_profit_1": zones.tp1.price,
            "take_profit_2": zones.tp2.price,
            "risk_reward_ratio": rr_ratio,
        },
    }


def _dedupe_overlaps(markers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort by quality, drop candidates overlapping already-claimed intervals."""
    markers.sort(key=lambda x: -x["quality"])
    clean: list[dict[str, Any]] = []
    claimed: list[tuple[int, int]] = []
    for m in markers:
        start, end = m["p0_idx"], m["p4_idx"]
        c_len = max(1, end - start)
        overlaps = any(
            max(0, min(end, e) - max(start, s)) > 0.10 * c_len for (s, e) in claimed
        )
        if not overlaps:
            clean.append(m)
            claimed.append((start, end))
    clean.sort(key=lambda x: x["time"])
    return clean
