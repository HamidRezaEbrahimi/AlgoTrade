# tests/test_pattern_rules.py
"""
Tests for the YAML rule-driven chart/wave pattern engine (app/strategy/patterns).

Covers:
1. Safe expression evaluation (comparisons, chained comparisons, arithmetic).
2. Injection & unknown-variable rejection with loud errors (no silent False).
3. Real rules_evaluation diagnostics (no fake `passed: True`).
4. End-to-end Bull Flag detection on synthetic candles via YAML rules.
5. Asset-class-aware impulse threshold resolution.
"""
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.models.candle import Candle
from app.strategy.patterns.rule_engine import (
    RuleConditionError,
    RuleEngine,
    evaluate_expression,
    get_detector_config,
    get_pattern_rules,
    resolve_impulse_min_pct,
)
from app.strategy.patterns.wave_classifier import scan_canonical_wave_patterns
from app.strategy.patterns.wave_points import build_features, calc_atr


# ──────────────────────────────────────────────
# Safe expression evaluation
# ──────────────────────────────────────────────
def test_evaluate_simple_comparison():
    assert evaluate_expression("a >= 1.5", {"a": 2.0}) is True
    assert evaluate_expression("a >= 1.5", {"a": 1.0}) is False
    assert evaluate_expression("a < b", {"a": 1, "b": 2}) is True


def test_evaluate_chained_comparison():
    features = {"a_retrace": 0.3}
    assert evaluate_expression("0.10 <= a_retrace <= 0.65", features) is True
    assert evaluate_expression("0.10 <= a_retrace <= 0.65", {"a_retrace": 0.05}) is False


def test_evaluate_arithmetic_right_side():
    assert evaluate_expression("disp >= p0_price * 0.018", {"disp": 10.0, "p0_price": 100.0}) is True
    assert evaluate_expression("disp >= p0_price * 0.018", {"disp": 1.0, "p0_price": 100.0}) is False


def test_evaluate_bool_equality():
    assert evaluate_expression("clean_impulse == True", {"clean_impulse": True}) is True
    assert evaluate_expression("clean_impulse == True", {"clean_impulse": False}) is False


def test_unknown_variable_raises_not_silent():
    with pytest.raises(RuleConditionError):
        evaluate_expression("unknown_var >= 1.0", {"a": 1.0})


def test_code_injection_rejected():
    with pytest.raises(RuleConditionError):
        evaluate_expression("__import__('os').system('echo pwned')", {})
    with pytest.raises(RuleConditionError):
        evaluate_expression("a.__class__", {"a": 1})


def test_syntax_error_raises():
    with pytest.raises(RuleConditionError):
        evaluate_expression("a >=* 1.0", {"a": 1.0})


# ──────────────────────────────────────────────
# Real rules_evaluation diagnostics
# ──────────────────────────────────────────────
def _features() -> dict:
    return {
        "p0_price": 100.0, "p1_price": 110.0, "p2_price": 107.2,
        "p3_price": 109.6, "p4_price": 106.6, "p5_price": 116.6,
        "disp": 10.0, "retrace_total": 0.34, "atr": 1.5,
        "flag_max_ret": 0.382, "flat_max_ret": 0.70, "risk_reward": 1.5,
        "clean_impulse": True, "a_retrace": 0.28, "b_over_a": 0.857,
        "c_over_a": 0.5, "a_drop": 2.8, "b_rise": 2.4, "c_drop": 3.0,
        "impulse_min_pct": 0.018,
        "time_ratio": 0.5,
        "range_ratio": 0.35,
        "B_breaks_i1_end": False,
        "C_breaks_A_end": True,
        "wave_b_candles": 3,
        "b_time": 4,
        "a_time": 3,
    }


def test_rule_engine_produces_real_diagnostics():
    engine = RuleEngine()
    rule = {
        "rule_id": "impulse_strength",
        "description": "impulse strength",
        "condition": "disp >= 1.5 * atr",
        "var_left": "disp",
        "var_right": "1.5 * atr",
    }
    evaluation = engine.evaluate_rule(rule, _features())
    assert evaluation.passed is True
    assert evaluation.value  # real computed value string, not hardcoded
    assert evaluation.value != "True"


def test_evaluate_pattern_fails_fast_on_failing_rule():
    engine = RuleEngine()
    pattern_def = {
        "id": "test",
        "rules": [
            {"rule_id": "r1", "condition": "disp >= 1.0", "var_left": "disp", "var_right": "1.0"},
            {"rule_id": "r2", "condition": "retrace_total <= flag_max_ret",
             "var_left": "retrace_total", "var_right": "flag_max_ret"},
        ],
    }
    features = _features()
    assert engine.evaluate_pattern(pattern_def, features) is not None

    features["retrace_total"] = 0.9  # breaks rule r2
    assert engine.evaluate_pattern(pattern_def, features) is None


def test_classify_uses_yaml_and_returns_evaluations():
    engine = RuleEngine()
    pattern_def, evaluations = engine.classify(_features(), "bullish")
    assert pattern_def is not None
    assert pattern_def["direction"] == "bullish"
    assert len(evaluations) > 0
    assert all(e.passed for e in evaluations)
    assert all(e.to_dict()["passed"] is True for e in evaluations)


def test_classify_no_match_returns_none():
    engine = RuleEngine()
    features = _features()
    # Break flag_bound rule in flag.yaml and flat rules
    features["time_ratio"] = 15.0
    features["a_retrace"] = 0.9
    features["range_ratio"] = 10.0
    pattern_def, _ = engine.classify(features, "bullish")
    assert pattern_def is None


# ──────────────────────────────────────────────
# YAML integrity & asset-class thresholds
# ──────────────────────────────────────────────
def test_yaml_rules_load_and_have_directions():
    rules = get_pattern_rules()
    assert len(rules) > 0
    assert all("direction" in r and "rules" in r for r in rules)


def test_detector_config_from_yaml():
    cfg = get_detector_config()
    assert cfg["min_impulse_atr"] == 1.5
    assert "impulse_min_pct_by_class" in cfg


def test_resolve_impulse_min_pct_by_asset_class():
    cfg = get_detector_config()
    assert resolve_impulse_min_pct(cfg, "crypto") == pytest.approx(0.005)
    assert resolve_impulse_min_pct(cfg, "forex") == pytest.approx(0.004)
    assert resolve_impulse_min_pct(cfg, "unknown") == pytest.approx(0.018)
    assert resolve_impulse_min_pct(cfg, None) == pytest.approx(0.018)


# ──────────────────────────────────────────────
# End-to-end Bull Flag detection on synthetic candles
# ──────────────────────────────────────────────
_BULL_FLAG_PATH = [
    # flat base, then impulse 100 -> 110 (10 candles impulse), correction A/B/C (6 candles), then drift
    100.0, 100.0, 100.0, 100.0, 100.0, 100.0,                # 0-5  (P0 = idx 5)
    101.0, 102.0, 103.0, 104.0, 105.0, 106.0,                # 6-11
    107.0, 108.0, 109.0, 110.0,                              # 12-15 (P1 = idx 15)
    108.6, 107.2,                                            # 16-17 (P2 = idx 17, wave A)
    108.4, 109.6,                                            # 15-16 (P3 = idx 16, wave B)
    108.0, 106.6,                                            # 17-18 (P4 = idx 18, wave C)
    106.6, 106.7, 106.6, 106.7, 106.6, 106.7,                # 19-24
    106.7, 106.7, 106.7, 106.7, 106.7, 106.7,                # 25-30
]


def _candles_from_path(path: list[float]) -> list[Candle]:
    base_ts = int(datetime(2025, 1, 1, tzinfo=UTC).timestamp())
    candles: list[Candle] = []
    for k, close in enumerate(path):
        open_ = path[k - 1] if k > 0 else close
        high = max(open_, close) + 0.05
        low = min(open_, close) - 0.05
        candles.append(
            Candle(
                symbol="BTCUSDT",
                timeframe="1h",
                timestamp=datetime.fromtimestamp(base_ts + k * 3600, tz=UTC),
                open=Decimal(str(open_)),
                high=Decimal(str(high)),
                low=Decimal(str(low)),
                close=Decimal(str(close)),
            )
        )
    return candles


def test_scan_detects_bull_flag_on_synthetic_candles():
    candles = _candles_from_path(_BULL_FLAG_PATH)
    assert len(candles) >= 25

    markers = scan_canonical_wave_patterns(candles)
    assert len(markers) > 0, "Rule-driven detector must find the synthetic Bull Flag"

    bull_flags = [
        m for m in markers
        if m["direction"] == "bullish" and m["category"] == "flag"
    ]
    assert bull_flags, "A bullish flag must be classified via YAML rules"

    flag = bull_flags[0]
    assert flag["name_en"] == "Flag"
    assert 2 <= flag["p0_idx"] <= 5
    assert 18 <= flag["p4_idx"] <= 21

    # REAL rules evaluation (legacy engine always returned passed=True)
    rules_eval = flag["rules_evaluation"]
    assert len(rules_eval) > 0
    assert all(r["passed"] is True for r in rules_eval)
    assert all(isinstance(r["value"], str) and r["value"] for r in rules_eval)

    # Full 6-point wave structure for chart drawing
    points = flag["points"]
    assert len(points) == 6
    assert [p["label"].split(" ")[0] for p in points] == ["P0", "P1", "P2", "P3", "P4", "P5"]
    assert flag["trade_setup"]["entry"] == pytest.approx(106.55)
    assert flag["trade_setup"]["stop_loss"] == pytest.approx(106.375)
    assert flag["trade_setup"]["take_profit_1"] > flag["trade_setup"]["entry"]


def test_scan_returns_nothing_on_flat_series():
    flat = [100.0] * 30
    markers = scan_canonical_wave_patterns(_candles_from_path(flat))
    assert markers == []


def test_scan_respects_min_candle_count():
    candles = _candles_from_path(_BULL_FLAG_PATH)[:20]
    assert scan_canonical_wave_patterns(candles) == []


def test_atr_matches_manual_benchmark():
    highs = [10.0, 11.0, 12.0, 11.5]
    lows = [9.0, 10.0, 11.0, 10.5]
    closes = [9.5, 10.5, 11.5, 11.0]
    # TR1 = max(1.0, |11-9.5|, |10-9.5|) = 1.5
    # TR2 = max(1.0, |12-10.5|, |11-10.5|) = 1.5
    # TR3 = max(1.0, |11.5-11.5|, |10.5-11.5|) = 1.0
    assert calc_atr(highs, lows, closes) == pytest.approx((1.5 + 1.5 + 1.0) / 3)


def test_build_features_direction_aware():
    cfg = get_detector_config()
    cycle = {
        "direction": "bullish",
        "p0_price": 100.0, "p1_price": 110.0, "p2_price": 107.2,
        "p3_price": 109.6, "p4_price": 106.6, "p5_price": 116.0,
        "p1_idx": 10, "p2_idx": 15, "p3_idx": 25, "p4_idx": 30,
        "disp": 10.0, "retrace_total": 0.34,
        "a_amp": 2.8, "b_amp": 2.4, "c_amp": 3.0,
    }
    features = build_features(cycle, atr=1.5, detector_cfg=cfg, impulse_min_pct=0.018)
    assert features["a_drop"] == pytest.approx(2.8)
    assert features["b_rise"] == pytest.approx(2.4)
    assert features["c_drop"] == pytest.approx(3.0)
    assert "a_rise" not in features
    assert features["b_over_a"] == pytest.approx(2.4 / 2.8)


def test_scan_rejects_sub_threshold_micro_noise():
    # Minor 0.5% move in consolidation: must NOT be detected as an impulse wave
    micro_path = [
        100.0, 100.0, 100.0,
        99.8, 99.6, 99.5,   # only 0.5% drop (under 1.8% threshold)
        99.7, 99.6, 99.7, 99.6, 99.7, 99.6, 99.7,
        99.6, 99.7, 99.6, 99.7, 99.6, 99.7, 99.6,
        99.7, 99.6, 99.7, 99.6, 99.7, 99.6, 99.7,
    ]
    candles = _candles_from_path(micro_path)
    markers = scan_canonical_wave_patterns(candles)
    assert markers == [], "Sub-threshold micro-movements must never produce pattern markers"
