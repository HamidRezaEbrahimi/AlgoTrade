# backend/app/strategy/alef_config.py
"""
Central configuration manager for AlefTrade Elliott Wave Engine.
Maintains persistent parameters for Running Flat, Regular Flat, Expanded Flat,
Adaptive ZigZag, Machine Learning Filters (Kaufman ER, Choppiness, DTW),
and Risk Management.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("algotrade.alef_config")

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config",
    "patterns",
    "alef_trade_config.json",
)

DEFAULT_ALEF_CONFIG: dict[str, Any] = {
    "running_flat": {
        "min_retr_a": 0.15,
        "max_retr_a": 0.85,
        "min_retr_b": 1.02,
        "max_retr_b": 2.50,
        "min_retr_c": 0.60,
        "max_retr_c": 1.05,
        "min_slope_ratio": 1.00,
        "enable_er_filter": False,
        "max_er_b": 0.40,
        "enable_chop": False,
        "min_chop": 50.0,
        "enable_dtw": False,
        "max_dtw": 0.35,
        "use_trend_filter": False,
        "trend_ema_len": 200,
    },
    "regular_flat": {
        "min_b": 0.90,
        "max_b": 1.05,
        "min_c": 0.90,
        "max_c": 1.05,
    },
    "expanded_flat": {
        "min_b": 1.05,
        "max_b": 1.382,
        "min_c": 1.05,
        "max_c": 1.618,
    },
    "zigzag": {
        "atr_period": 14,
        "atr_multiplier": 2.0,
        "atr_mult_macro": 2.6,
        "atr_mult_base": 1.8,
        "auto_timeframe_mult": True,
    },
    "risk_manager": {
        "enable_break_even": True,
        "be_trigger_r": 1.0,
        "trailing_mode": "STEP_R",
        "step_r_min_trigger": 1.5,
        "step_r_lock_buffer": 1.0,
        "tp2_fib": 1.272,
        "enable_dynamic_tp": True,
    },
}

_CACHED_CONFIG: dict[str, Any] | None = None


def load_alef_trade_config() -> dict[str, Any]:
    """Load and merge persisted AlefTrade config with defaults."""
    global _CACHED_CONFIG
    if _CACHED_CONFIG is not None:
        return _CACHED_CONFIG

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                merged = {**DEFAULT_ALEF_CONFIG}
                for k, v in saved.items():
                    if isinstance(v, dict) and k in merged:
                        merged[k] = {**merged[k], **v}
                    else:
                        merged[k] = v
                _CACHED_CONFIG = merged
                return _CACHED_CONFIG
        except Exception as e:
            logger.warning("Could not read %s: %s; using defaults", CONFIG_PATH, e)

    _CACHED_CONFIG = dict(DEFAULT_ALEF_CONFIG)
    return _CACHED_CONFIG


def save_alef_trade_config(new_config: dict[str, Any]) -> None:
    """Save updated AlefTrade configuration to JSON file."""
    global _CACHED_CONFIG
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    current = load_alef_trade_config()
    for k, v in new_config.items():
        if isinstance(v, dict) and k in current:
            current[k] = {**current[k], **v}
        else:
            current[k] = v

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)

    _CACHED_CONFIG = current


def build_alef_rules_payload() -> list[dict[str, Any]]:
    """Convert AlefTrade configurations to UI-compatible pattern rules list."""
    cfg = load_alef_trade_config()
    rf = cfg.get("running_flat", {})
    reg = cfg.get("regular_flat", {})
    exp = cfg.get("expanded_flat", {})
    zz = cfg.get("zigzag", {})
    rm = cfg.get("risk_manager", {})

    patterns = [
        # 1. Running Flat (Bullish & Bearish)
        {
            "id": "running_flat_bullish",
            "name_en": "Running Flat (Bullish)",
            "name_fa": "الگوی فلت دونده (صعودی)",
            "category": "running_flat",
            "direction": "bullish",
            "ratios": [
                {"key": "min_retr_a", "title_fa": "حداقل اصلاح A", "title_en": "Min Wave A Retr", "min": 0.1, "max": 0.5, "typical": rf.get("min_retr_a", 0.15)},
                {"key": "max_retr_a", "title_fa": "حداکثر اصلاح A", "title_en": "Max Wave A Retr", "min": 0.5, "max": 0.95, "typical": rf.get("max_retr_a", 0.85)},
                {"key": "min_retr_b", "title_fa": "حداقل شکست B", "title_en": "Min Wave B Retr", "min": 1.0, "max": 1.5, "typical": rf.get("min_retr_b", 1.02)},
                {"key": "max_retr_b", "title_fa": "حداکثر انبساط B", "title_en": "Max Wave B Retr", "min": 1.5, "max": 3.0, "typical": rf.get("max_retr_b", 2.50)},
                {"key": "min_retr_c", "title_fa": "کف PRZ موج C", "title_en": "Min PRZ Wave C", "min": 0.4, "max": 0.8, "typical": rf.get("min_retr_c", 0.60)},
                {"key": "max_retr_c", "title_fa": "سقف PRZ موج C", "title_en": "Max PRZ Wave C", "min": 0.8, "max": 1.2, "typical": rf.get("max_retr_c", 1.05)},
            ],
            "thresholds": [
                {"key": "min_slope_ratio", "title_fa": "حداقل شتاب زمانی", "title_en": "Min Slope Ratio", "min": 0.5, "typical": rf.get("min_slope_ratio", 1.0)},
                {"key": "max_er_b", "title_fa": "سقف کارایی کافمن", "title_en": "Max Kaufman ER", "min": 0.1, "typical": rf.get("max_er_b", 0.40)},
                {"key": "min_chop", "title_fa": "حداقل شاخص فشردگی", "title_en": "Min Chop Index", "min": 30.0, "typical": rf.get("min_chop", 50.0)},
                {"key": "max_dtw", "title_fa": "سقف فاصله انطباق DTW", "title_en": "Max DTW Distance", "min": 0.1, "typical": rf.get("max_dtw", 0.35)},
            ],
            "rules": [
                {"rule_id": "rf_bull_rule1", "group": "structure", "description": "موج B کف موج P1 را با مومنتوم می‌شکند", "condition": "B.price < P1.price", "var_left": "B.price", "operator": "<", "var_right": "P1.price"},
                {"rule_id": "rf_bull_rule2", "group": "structure", "description": "موج C درون باند PRZ (0.60 تا 1.05 موج B) متوقف می‌شود", "condition": "C.retr_b >= 0.60 && C.retr_b <= 1.05", "var_left": "C.retr_b", "operator": "between", "var_right": "0.60, 1.05"},
                {"rule_id": "rf_bull_rule3", "group": "structure", "description": "استاپ لاس زیر کف اکستریم موج B ست می‌شود", "condition": "SL < B.price", "var_left": "SL", "operator": "<", "var_right": "B.price"},
            ],
        },
        {
            "id": "running_flat_bearish",
            "name_en": "Running Flat (Bearish)",
            "name_fa": "الگوی فلت دونده (نزولی)",
            "category": "running_flat",
            "direction": "bearish",
            "ratios": [
                {"key": "min_retr_a", "title_fa": "حداقل اصلاح A", "title_en": "Min Wave A Retr", "min": 0.1, "max": 0.5, "typical": rf.get("min_retr_a", 0.15)},
                {"key": "max_retr_a", "title_fa": "حداکثر اصلاح A", "title_en": "Max Wave A Retr", "min": 0.5, "max": 0.95, "typical": rf.get("max_retr_a", 0.85)},
                {"key": "min_retr_b", "title_fa": "حداقل شکست B", "title_en": "Min Wave B Retr", "min": 1.0, "max": 1.5, "typical": rf.get("min_retr_b", 1.02)},
                {"key": "max_retr_b", "title_fa": "حداکثر انبساط B", "title_en": "Max Wave B Retr", "min": 1.5, "max": 3.0, "typical": rf.get("max_retr_b", 2.50)},
                {"key": "min_retr_c", "title_fa": "کف PRZ موج C", "title_en": "Min PRZ Wave C", "min": 0.4, "max": 0.8, "typical": rf.get("min_retr_c", 0.60)},
                {"key": "max_retr_c", "title_fa": "سقف PRZ موج C", "title_en": "Max PRZ Wave C", "min": 0.8, "max": 1.2, "typical": rf.get("max_retr_c", 1.05)},
            ],
            "thresholds": [
                {"key": "min_slope_ratio", "title_fa": "حداقل شتاب زمانی", "title_en": "Min Slope Ratio", "min": 0.5, "typical": rf.get("min_slope_ratio", 1.0)},
                {"key": "max_er_b", "title_fa": "سقف کارایی کافمن", "title_en": "Max Kaufman ER", "min": 0.1, "typical": rf.get("max_er_b", 0.40)},
                {"key": "min_chop", "title_fa": "حداقل شاخص فشردگی", "title_en": "Min Chop Index", "min": 30.0, "typical": rf.get("min_chop", 50.0)},
                {"key": "max_dtw", "title_fa": "سقف فاصله انطباق DTW", "title_en": "Max DTW Distance", "min": 0.1, "typical": rf.get("max_dtw", 0.35)},
            ],
            "rules": [
                {"rule_id": "rf_bear_rule1", "group": "structure", "description": "موج B سقف موج P1 را با مومنتوم می‌شکند", "condition": "B.price > P1.price", "var_left": "B.price", "operator": ">", "var_right": "P1.price"},
                {"rule_id": "rf_bear_rule2", "group": "structure", "description": "موج C درون باند PRZ (0.60 تا 1.05 موج B) متوقف می‌شود", "condition": "C.retr_b >= 0.60 && C.retr_b <= 1.05", "var_left": "C.retr_b", "operator": "between", "var_right": "0.60, 1.05"},
                {"rule_id": "rf_bear_rule3", "group": "structure", "description": "استاپ لاس بالای سقف اکستریم موج B ست می‌شود", "condition": "SL > B.price", "var_left": "SL", "operator": ">", "var_right": "B.price"},
            ],
        },
        # 2. Regular Flat
        {
            "id": "regular_flat_bullish",
            "name_en": "Regular Flat (Bullish)",
            "name_fa": "الگوی فلت عادی (صعودی)",
            "category": "regular_flat",
            "direction": "bullish",
            "ratios": [
                {"key": "min_b", "title_fa": "حداقل موج B", "title_en": "Min Wave B", "min": 0.8, "max": 1.0, "typical": reg.get("min_b", 0.90)},
                {"key": "max_b", "title_fa": "حداکثر موج B", "title_en": "Max Wave B", "min": 1.0, "max": 1.1, "typical": reg.get("max_b", 1.05)},
                {"key": "min_c", "title_fa": "حداقل موج C", "title_en": "Min Wave C", "min": 0.8, "max": 1.0, "typical": reg.get("min_c", 0.90)},
                {"key": "max_c", "title_fa": "حداکثر موج C", "title_en": "Max Wave C", "min": 1.0, "max": 1.15, "typical": reg.get("max_c", 1.05)},
            ],
            "thresholds": [],
            "rules": [
                {"rule_id": "reg_rule1", "group": "structure", "description": "موج B تقریباً برابر با موج A بازگشت می‌کند", "condition": "B_retr_A >= 0.90 && B_retr_A <= 1.05", "var_left": "B_retr_A", "operator": "between", "var_right": "0.90, 1.05"},
                {"rule_id": "reg_rule2", "group": "structure", "description": "موج C در نزدیکی انتهای موج A خاتمه می‌یابد", "condition": "C_retr_B >= 0.90 && C_retr_B <= 1.05", "var_left": "C_retr_B", "operator": "between", "var_right": "0.90, 1.05"},
            ],
        },
        {
            "id": "regular_flat_bearish",
            "name_en": "Regular Flat (Bearish)",
            "name_fa": "الگوی فلت عادی (نزولی)",
            "category": "regular_flat",
            "direction": "bearish",
            "ratios": [
                {"key": "min_b", "title_fa": "حداقل موج B", "title_en": "Min Wave B", "min": 0.8, "max": 1.0, "typical": reg.get("min_b", 0.90)},
                {"key": "max_b", "title_fa": "حداکثر موج B", "title_en": "Max Wave B", "min": 1.0, "max": 1.1, "typical": reg.get("max_b", 1.05)},
                {"key": "min_c", "title_fa": "حداقل موج C", "title_en": "Min Wave C", "min": 0.8, "max": 1.0, "typical": reg.get("min_c", 0.90)},
                {"key": "max_c", "title_fa": "حداکثر موج C", "title_en": "Max Wave C", "min": 1.0, "max": 1.15, "typical": reg.get("max_c", 1.05)},
            ],
            "thresholds": [],
            "rules": [
                {"rule_id": "reg_rule1", "group": "structure", "description": "موج B تقریباً برابر با موج A بازگشت می‌کند", "condition": "B_retr_A >= 0.90 && B_retr_A <= 1.05", "var_left": "B_retr_A", "operator": "between", "var_right": "0.90, 1.05"},
                {"rule_id": "reg_rule2", "group": "structure", "description": "موج C در نزدیکی انتهای موج A خاتمه می‌یابد", "condition": "C_retr_B >= 0.90 && C_retr_B <= 1.05", "var_left": "C_retr_B", "operator": "between", "var_right": "0.90, 1.05"},
            ],
        },
        # 3. Expanded Flat
        {
            "id": "expanded_flat_bullish",
            "name_en": "Expanded Flat (Bullish)",
            "name_fa": "الگوی فلت منبسط (صعودی)",
            "category": "expanded_flat",
            "direction": "bullish",
            "ratios": [
                {"key": "min_b", "title_fa": "نفوذ موج B", "title_en": "Min Wave B", "min": 1.05, "max": 1.2, "typical": exp.get("min_b", 1.05)},
                {"key": "max_b", "title_fa": "سقف نفوذ B", "title_en": "Max Wave B", "min": 1.2, "max": 1.6, "typical": exp.get("max_b", 1.382)},
                {"key": "min_c", "title_fa": "نفوذ موج C", "title_en": "Min Wave C", "min": 1.05, "max": 1.3, "typical": exp.get("min_c", 1.05)},
                {"key": "max_c", "title_fa": "سقف نفوذ C", "title_en": "Max Wave C", "min": 1.3, "max": 2.0, "typical": exp.get("max_c", 1.618)},
            ],
            "thresholds": [],
            "rules": [
                {"rule_id": "exp_rule1", "group": "structure", "description": "موج B فراتر از شروع موج A نفوذ می‌کند (1.05 تا 1.382)", "condition": "B_retr_A > 1.05", "var_left": "B_retr_A", "operator": ">", "var_right": "1.05"},
                {"rule_id": "exp_rule2", "group": "structure", "description": "موج C فراتر از انتهای موج A حرکت می‌کند (1.05 تا 1.618)", "condition": "C_retr_B > 1.05", "var_left": "C_retr_B", "operator": ">", "var_right": "1.05"},
            ],
        },
        {
            "id": "expanded_flat_bearish",
            "name_en": "Expanded Flat (Bearish)",
            "name_fa": "الگوی فلت منبسط (نزولی)",
            "category": "expanded_flat",
            "direction": "bearish",
            "ratios": [
                {"key": "min_b", "title_fa": "نفوذ موج B", "title_en": "Min Wave B", "min": 1.05, "max": 1.2, "typical": exp.get("min_b", 1.05)},
                {"key": "max_b", "title_fa": "سقف نفوذ B", "title_en": "Max Wave B", "min": 1.2, "max": 1.6, "typical": exp.get("max_b", 1.382)},
                {"key": "min_c", "title_fa": "نفوذ موج C", "title_en": "Min Wave C", "min": 1.05, "max": 1.3, "typical": exp.get("min_c", 1.05)},
                {"key": "max_c", "title_fa": "سقف نفوذ C", "title_en": "Max Wave C", "min": 1.3, "max": 2.0, "typical": exp.get("max_c", 1.618)},
            ],
            "thresholds": [],
            "rules": [
                {"rule_id": "exp_rule1", "group": "structure", "description": "موج B فراتر از شروع موج A نفوذ می‌کند (1.05 تا 1.382)", "condition": "B_retr_A > 1.05", "var_left": "B_retr_A", "operator": ">", "var_right": "1.05"},
                {"rule_id": "exp_rule2", "group": "structure", "description": "موج C فراتر از انتهای موج A حرکت می‌کند (1.05 تا 1.618)", "condition": "C_retr_B > 1.05", "var_left": "C_retr_B", "operator": ">", "var_right": "1.05"},
            ],
        },
        # 4. Multi-scale Adaptive ZigZag
        {
            "id": "zigzag_bullish",
            "name_en": "Adaptive ZigZag (Bullish)",
            "name_fa": "موتور چندمقیاسی زیگزاگ",
            "category": "zigzag",
            "direction": "bullish",
            "ratios": [
                {"key": "atr_multiplier", "title_fa": "ضریب عمومی ATR", "title_en": "General ATR Mult", "min": 1.0, "max": 4.0, "typical": zz.get("atr_multiplier", 2.0)},
                {"key": "atr_mult_macro", "title_fa": "ضریب ATR ماکرو", "title_en": "Macro ATR Mult", "min": 2.0, "max": 5.0, "typical": zz.get("atr_mult_macro", 2.6)},
                {"key": "atr_mult_base", "title_fa": "ضریب ATR پایه", "title_en": "Base ATR Mult", "min": 1.2, "max": 3.0, "typical": zz.get("atr_mult_base", 1.8)},
            ],
            "thresholds": [
                {"key": "atr_period", "title_fa": "دوره محاسبه ATR", "title_en": "ATR Period", "min": 5, "typical": zz.get("atr_period", 14)},
            ],
            "rules": [
                {"rule_id": "zz_rule1", "group": "structure", "description": "تشخیص پیوت‌های ماکرو برای ساختار کلی امواج", "condition": "pivots_macro.length >= 3", "var_left": "pivots_macro.length", "operator": ">=", "var_right": "3"},
            ],
        },
        {
            "id": "zigzag_bearish",
            "name_en": "Adaptive ZigZag (Bearish)",
            "name_fa": "موتور چندمقیاسی زیگزاگ",
            "category": "zigzag",
            "direction": "bearish",
            "ratios": [
                {"key": "atr_multiplier", "title_fa": "ضریب عمومی ATR", "title_en": "General ATR Mult", "min": 1.0, "max": 4.0, "typical": zz.get("atr_multiplier", 2.0)},
                {"key": "atr_mult_macro", "title_fa": "ضریب ATR ماکرو", "title_en": "Macro ATR Mult", "min": 2.0, "max": 5.0, "typical": zz.get("atr_mult_macro", 2.6)},
                {"key": "atr_mult_base", "title_fa": "ضریب ATR پایه", "title_en": "Base ATR Mult", "min": 1.2, "max": 3.0, "typical": zz.get("atr_mult_base", 1.8)},
            ],
            "thresholds": [
                {"key": "atr_period", "title_fa": "دوره محاسبه ATR", "title_en": "ATR Period", "min": 5, "typical": zz.get("atr_period", 14)},
            ],
            "rules": [
                {"rule_id": "zz_rule1", "group": "structure", "description": "تشخیص پیوت‌های ماکرو برای ساختار کلی امواج", "condition": "pivots_macro.length >= 3", "var_left": "pivots_macro.length", "operator": ">=", "var_right": "3"},
            ],
        },
        # 5. Risk Manager & Trailing Stop
        {
            "id": "risk_manager_bullish",
            "name_en": "Risk Manager (Bullish)",
            "name_fa": "مدیریت ریسک و خروج",
            "category": "risk_manager",
            "direction": "bullish",
            "ratios": [
                {"key": "be_trigger_r", "title_fa": "تریگر ریسک‌فری (R)", "title_en": "Break Even Trigger R", "min": 0.5, "max": 2.5, "typical": rm.get("be_trigger_r", 1.0)},
                {"key": "step_r_min_trigger", "title_fa": "تریگر تریلینگ (R)", "title_en": "Step-R Trigger R", "min": 1.0, "max": 3.0, "typical": rm.get("step_r_min_trigger", 1.5)},
                {"key": "step_r_lock_buffer", "title_fa": "بافر قفل سود (R)", "title_en": "Lock Buffer R", "min": 0.5, "max": 2.0, "typical": rm.get("step_r_lock_buffer", 1.0)},
                {"key": "tp2_fib", "title_fa": "تارگت ۲ فیبوناچی", "title_en": "TP2 Fib Extension", "min": 1.1, "max": 2.0, "typical": rm.get("tp2_fib", 1.272)},
            ],
            "thresholds": [],
            "rules": [
                {"rule_id": "rm_rule1", "group": "structure", "description": "انتقال استاپ به نقطه ورود پس از رسیدن به 1R", "condition": "current_r >= be_trigger_r", "var_left": "current_r", "operator": ">=", "var_right": "1.0"},
                {"rule_id": "rm_rule2", "group": "structure", "description": "قفل ۵۰٪ سود در تراز TP1", "condition": "price >= tp1", "var_left": "price", "operator": ">=", "var_right": "tp1"},
            ],
        },
        {
            "id": "risk_manager_bearish",
            "name_en": "Risk Manager (Bearish)",
            "name_fa": "مدیریت ریسک و خروج",
            "category": "risk_manager",
            "direction": "bearish",
            "ratios": [
                {"key": "be_trigger_r", "title_fa": "تریگر ریسک‌فری (R)", "title_en": "Break Even Trigger R", "min": 0.5, "max": 2.5, "typical": rm.get("be_trigger_r", 1.0)},
                {"key": "step_r_min_trigger", "title_fa": "تریگر تریلینگ (R)", "title_en": "Step-R Trigger R", "min": 1.0, "max": 3.0, "typical": rm.get("step_r_min_trigger", 1.5)},
                {"key": "step_r_lock_buffer", "title_fa": "بافر قفل سود (R)", "title_en": "Lock Buffer R", "min": 0.5, "max": 2.0, "typical": rm.get("step_r_lock_buffer", 1.0)},
                {"key": "tp2_fib", "title_fa": "تارگت ۲ فیبوناچی", "title_en": "TP2 Fib Extension", "min": 1.1, "max": 2.0, "typical": rm.get("tp2_fib", 1.272)},
            ],
            "thresholds": [],
            "rules": [
                {"rule_id": "rm_rule1", "group": "structure", "description": "انتقال استاپ به نقطه ورود پس از رسیدن به 1R", "condition": "current_r >= be_trigger_r", "var_left": "current_r", "operator": ">=", "var_right": "1.0"},
                {"rule_id": "rm_rule2", "group": "structure", "description": "قفل ۵۰٪ سود در تراز TP1", "condition": "price <= tp1", "var_left": "price", "operator": "<=", "var_right": "tp1"},
            ],
        },
    ]
    return patterns
