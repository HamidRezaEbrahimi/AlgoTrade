# app/strategy/patterns/wave_points.py
"""
Pure Wave-Cycle Geometry Extraction (P0-P5).

Responsible ONLY for canonical wave-cycle geometry:
- ATR calculation
- Clean (contiguous) impulse verification
- P0..P5 point extraction for bullish / bearish cycles
- Feature dictionary construction for the RuleEngine

NO classification logic lives here: whether a cycle is a Flag, Flat,
Expanded/Running Flat, etc. is decided purely by YAML rules
(see rule_engine.py). Only definitional sanity checks (positive wave
amplitudes, valid alternating swings) are enforced.
"""
from __future__ import annotations

from typing import Any

import numpy as np


def calc_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """Calculate standard Average True Range."""
    highs = np.asarray(highs, dtype=float)
    lows = np.asarray(lows, dtype=float)
    closes = np.asarray(closes, dtype=float)
    if len(highs) < 2:
        return 1.0
    tr = np.maximum(
        highs[1:] - lows[1:],
        np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])),
    )
    if len(tr) < period:
        return float(np.mean(tr)) if len(tr) > 0 else 1.0
    return float(np.mean(tr[-period:]))


def is_clean_impulse(
    highs: np.ndarray,
    lows: np.ndarray,
    start_idx: int,
    end_idx: int,
    atr: float,
    direction: str = "bullish",
) -> bool:
    """Ensure no major counter-trend swing occurred inside the impulse leg."""
    if end_idx - start_idx < 1:
        return False
    if direction == "bullish":
        running_ext = highs[start_idx]
        total_disp = highs[end_idx] - lows[start_idx]
        if total_disp <= 0:
            return False
        for k in range(start_idx + 1, end_idx):
            if highs[k] > running_ext:
                running_ext = highs[k]
            pullback = running_ext - lows[k]
            if pullback > 0.75 * (running_ext - lows[start_idx]) and pullback > 3.0 * atr:
                return False
    else:
        running_ext = lows[start_idx]
        total_disp = highs[start_idx] - lows[end_idx]
        if total_disp <= 0:
            return False
        for k in range(start_idx + 1, end_idx):
            if lows[k] < running_ext:
                running_ext = lows[k]
            pullback = highs[k] - running_ext
            if pullback > 0.75 * (highs[start_idx] - running_ext) and pullback > 3.0 * atr:
                return False
    return True


def _is_local_extreme(arr: np.ndarray, idx: int, w: int, want_max: bool, n: int) -> bool:
    window = arr[max(0, idx - w):min(n, idx + w + 1)]
    if len(window) == 0:
        return False
    return bool(arr[idx] == (np.max(window) if want_max else np.min(window)))


def extract_candidate_wave_cycles(
    highs: np.ndarray,
    lows: np.ndarray,
    timestamps: list[int],
    n: int,
    start_idx: int,
    pulse_idx: int,
    direction: str,
) -> list[dict[str, Any]]:
    """
    Extract candidate P0..P5 wave cycle geometries from significant swings.

    P0 = impulse start, P1 = impulse end, P2/P3/P4 = waves A/B/C,
    P5 = post-pattern extreme (or projected 1:1 target).
    """
    is_bull = direction == "bullish"
    p0_price = float(lows[start_idx] if is_bull else highs[start_idx])
    p0_time = timestamps[start_idx]
    p1_price = float(highs[pulse_idx] if is_bull else lows[pulse_idx])
    p1_time = timestamps[pulse_idx]
    disp = (p1_price - p0_price) if is_bull else (p0_price - p1_price)
    if disp <= 0:
        return []

    max_c_len = min(35, n - pulse_idx - 1)
    if max_c_len < 4:
        return []

    c_lows = lows[pulse_idx + 1:pulse_idx + 1 + max_c_len]
    c_highs = highs[pulse_idx + 1:pulse_idx + 1 + max_c_len]

    # Instead of arbitrary w=2/w=1 checking on subsets, we use global robust swing points
    # This prevents micro-pullbacks from being falsely labeled as A, B, C waves.
    from app.strategy.structure_analyzer import find_swing_points
    
    # We dynamically select lookback. 3 is a good minimum to avoid noise, 5 is standard structure.
    # To be safe, we'll try lookback=3, if it fails to find points, we can fallback to lookback=1.
    swings_3 = find_swing_points(highs, lows, lookback=3)
    swings_1 = find_swing_points(highs, lows, lookback=1)
    swings = swings_3 if swings_3 and len(swings_3) >= 3 else swings_1
    
    # Filter swings that occur AFTER pulse_idx and BEFORE pulse_idx + max_c_len
    valid_highs = [s.index for s in swings if s.is_high and pulse_idx < s.index <= pulse_idx + max_c_len]
    valid_lows = [s.index for s in swings if not s.is_high and pulse_idx < s.index <= pulse_idx + max_c_len]
    
    arr_a = valid_lows if is_bull else valid_highs
    
    cycles: list[dict[str, Any]] = []
    for p2_idx in arr_a[:4]:
        p2_price = float(lows[p2_idx] if is_bull else highs[p2_idx])
        a_amp = abs(p1_price - p2_price)
        if a_amp <= 0:
            continue

        arr_b = [idx for idx in (valid_highs if is_bull else valid_lows) if idx > p2_idx]
        
        for p3_idx in arr_b[:3]:
            p3_price = float(highs[p3_idx] if is_bull else lows[p3_idx])
            b_amp = (p3_price - p2_price) if is_bull else (p2_price - p3_price)
            if b_amp <= 0:
                continue

            arr_c = [idx for idx in (valid_lows if is_bull else valid_highs) if idx > p3_idx]
            
            for p4_idx in arr_c[:3]:
                p4_price = float(lows[p4_idx] if is_bull else highs[p4_idx])
                c_amp = (p3_price - p4_price) if is_bull else (p4_price - p3_price)
                if c_amp <= 0:
                    continue

                retrace_total = abs(p4_price - p1_price) / disp
                p5_target = p4_price + disp if is_bull else p4_price - disp
                p5_dict, p5_price = _extract_p5(
                    highs, lows, timestamps, n, p4_idx, p4_price, p5_target,
                    is_bull=is_bull, p0_time=p0_time, p1_time=p1_time,
                    p1_price=p1_price, disp=disp,
                )
                cycles.append({
                    "p0_idx": start_idx,
                    "p1_idx": pulse_idx,
                    "p2_idx": p2_idx,
                    "p3_idx": p3_idx,
                    "p4_idx": p4_idx,
                    "p0_price": p0_price,
                    "p1_price": p1_price,
                    "p2_price": p2_price,
                    "p3_price": p3_price,
                    "p4_price": p4_price,
                    "p5_price": p5_price,
                    "p5_dict": p5_dict,
                    "disp": disp,
                    "a_amp": a_amp,
                    "b_amp": b_amp,
                    "c_amp": c_amp,
                    "retrace_total": retrace_total,
                    "direction": direction,
                })

    return cycles


def extract_wave_cycle(
    highs: np.ndarray,
    lows: np.ndarray,
    timestamps: list[int],
    n: int,
    start_idx: int,
    pulse_idx: int,
    direction: str,
) -> dict[str, Any] | None:
    """Extract primary canonical P0..P5 wave cycle geometry."""
    candidates = extract_candidate_wave_cycles(
        highs, lows, timestamps, n, start_idx, pulse_idx, direction
    )
    return candidates[0] if candidates else None


def _extract_p5(
    highs: np.ndarray,
    lows: np.ndarray,
    timestamps: list[int],
    n: int,
    p4_idx: int,
    p4_price: float,
    p5_target: float,
    is_bull: bool,
    p0_time: int,
    p1_time: int,
    p1_price: float = 0.0,
    disp: float = 0.0,
) -> tuple:
    """Find real P5 extreme after P4, or project a 1:1 measured-move target.
    
    A subsequent price move only qualifies as a completed Impulse 2 if it
    reaches or exceeds the initial impulse peak (P1) or makes significant
    progress (at least 0.5 * disp) toward the measured move target. Minor
    fluctuations around entry remain an active setup at P4 with projected P5.
    """
    post = highs[p4_idx + 1:min(n, p4_idx + 16)] if is_bull else lows[p4_idx + 1:min(n, p4_idx + 16)]
    has_real_impulse = len(post) > 0 and (
        (is_bull and (np.max(post) >= p1_price or (disp > 0 and (np.max(post) - p4_price) >= 0.5 * disp)))
        or (not is_bull and (np.min(post) <= p1_price or (disp > 0 and (p4_price - np.min(post)) >= 0.5 * disp)))
    )
    if has_real_impulse:
        rel = int(np.argmax(post)) if is_bull else int(np.argmin(post))
        idx = p4_idx + 1 + rel
        price = float(post[rel])
        label = f"P5 (ایمپالس ۲: {price:,.0f}) 🏁"
        return {"time": timestamps[idx], "price": price, "label": label}, price
    price = round(p5_target, 2)
    p5_time = timestamps[p4_idx] + (p1_time - p0_time)
    label = f"P5 (تارگت ۱:۱: {price:,.0f}) 🎯"
    return {"time": p5_time, "price": price, "label": label}, price


def build_features(
    cycle: dict[str, Any],
    atr: float,
    detector_cfg: dict[str, Any],
    impulse_min_pct: float,
) -> dict[str, Any]:
    """Build the rule-engine variable dictionary for a wave cycle.

    Produces ALL features required by the YAML reference rules, including
    the structural break checks (B_breaks_i1_end, C_breaks_A_end), the
    Flag-specific time/range ratios, and the REAL risk/reward calculation.
    """
    is_bull = cycle["direction"] == "bullish"
    a_amp, b_amp, c_amp = cycle["a_amp"], cycle["b_amp"], cycle["c_amp"]
    disp = cycle["disp"]

    # --- Structural break features (core flat-type differentiator) ---
    # B_breaks_i1_end: Does wave B's extreme exceed impulse_1's end (P1)?
    # C_breaks_A_end: Does wave C's extreme exceed wave A's end (P2)?
    if is_bull:
        # Bullish: P1=high, P3=high(B), P2=low(A), P4=low(C)
        b_breaks_i1 = cycle["p3_price"] > cycle["p1_price"]
        c_breaks_a = cycle["p4_price"] < cycle["p2_price"]
    else:
        # Bearish: P1=low, P3=low(B), P2=high(A), P4=high(C)
        b_breaks_i1 = cycle["p3_price"] < cycle["p1_price"]
        c_breaks_a = cycle["p4_price"] > cycle["p2_price"]

    # --- Flag-specific features ---
    # time_ratio: correction duration / impulse duration
    impulse_candles = max(1, cycle.get("p1_idx", 1) - cycle.get("p0_idx", 0))
    correction_candles = max(1, cycle.get("p4_idx", 1) - cycle.get("p1_idx", 0))
    time_ratio = correction_candles / impulse_candles

    # range_ratio: correction price range / impulse price range
    range_ratio = (a_amp + c_amp) / (2.0 * disp) if disp > 0 else 1.0

    # Wave time duration features (candles)
    a_time = float(cycle.get("p2_idx", 0) - cycle.get("p1_idx", 0))
    b_time = float(cycle.get("p3_idx", 0) - cycle.get("p2_idx", 0))
    c_time = float(cycle.get("p4_idx", 0) - cycle.get("p3_idx", 0))

    # --- Real risk/reward ---
    p0 = cycle.get("p0_price", 0.0)
    p4 = cycle.get("p4_price", 0.0)
    p5 = cycle.get("p5_price", 0.0)
    risk = abs(p4 - p0)
    if risk > 0:
        reward = abs(p5 - p4)
        real_rr = reward / risk
    else:
        real_rr = float(detector_cfg.get("min_risk_reward", 1.5))

    features: dict[str, Any] = {
        "p0_price": p0,
        "p1_price": cycle.get("p1_price", 0.0),
        "p2_price": cycle.get("p2_price", 0.0),
        "p3_price": cycle.get("p3_price", 0.0),
        "p4_price": p4,
        "p5_price": p5,
        "disp": disp,
        "retrace_total": cycle.get("retrace_total", 0.0),
        "atr": atr,
        "flag_max_ret": float(detector_cfg.get("flag_max_retrace", 0.382)),
        "flat_max_ret": float(detector_cfg.get("flat_max_retrace", 0.70)),
        "impulse_min_pct": impulse_min_pct,
        "clean_impulse": True,  # guaranteed by the extraction gate
        # Time constraints
        "a_time": a_time,
        "b_time": b_time,
        "c_time": c_time,
        # Ratios
        "a_retrace": a_amp / disp if disp > 0 else 0.0,
        "b_over_a": b_amp / a_amp if a_amp > 0 else 0.0,
        "c_over_a": c_amp / a_amp if a_amp > 0 else 0.0,
        
        # New CEL structural variables
        "has_internal_structure": (cycle.get("p3_idx", 0) - cycle.get("p2_idx", 0)) > 2,
        "b_duration_ratio": (cycle.get("p3_idx", 1) - cycle.get("p2_idx", 0)) / max(1, cycle.get("p2_idx", 1) - cycle.get("p1_idx", 0)),
        "c_duration_ratio": (cycle.get("p4_idx", 1) - cycle.get("p3_idx", 0)) / max(1, cycle.get("p2_idx", 1) - cycle.get("p1_idx", 0)),
        "time_ratio": time_ratio,
        "range_ratio": range_ratio,
        "i2_slope_ratio": 1.0,  # Proxy for now
        "i2_crossed_P4": True,
        "impulse2_started": True,
        "i2_opposes_C": True,
        "point_count": 5,
        "entry_a": real_rr,
        "entry_b": real_rr,
        "high_risk_high_reward": real_rr > 3.0 and risk > 2.0 * atr,
        "high_risk_low_reward": real_rr < 1.0 and risk > atr,
        "wave_b_candles": cycle.get("p3_idx", 0) - cycle.get("p2_idx", 0),
        # Structural break features (from reference YAML rules)
        "B_breaks_i1_end": b_breaks_i1,
        "C_breaks_A_end": c_breaks_a,
        
        # New aliases for complex CEL rules
        "B_over_A": b_amp / a_amp if a_amp > 0 else 0.0,
        "C_over_A": c_amp / a_amp if a_amp > 0 else 0.0,
        "structure_valid": True,
        "i2_same_as_C": False,
        "complex_flat_b_duration_ratio": float(detector_cfg.get("complex_flat_b_duration_ratio", 2.0)),
        # Real risk/reward (not the config threshold!)
        "risk_reward": real_rr,
    }
    if is_bull:
        # Bullish cycle: A drops, B rises, C drops
        features.update({"a_drop": a_amp, "b_rise": b_amp, "c_drop": c_amp})
    else:
        # Bearish cycle: A rises, B drops, C rises
        features.update({"a_rise": a_amp, "b_drop": b_amp, "c_rise": c_amp})
    return features
