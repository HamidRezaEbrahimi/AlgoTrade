# app/market_data/market_analyzer.py
"""
Live Multi-Timeframe Market & 8-Criteria Real-Time Analyzer.

Delegates to the REAL strategy-engine modules (structure_analyzer,
level_detector, pattern_detector, momentum_filter) and stateless indicators
(RSI, ATR, volume) — no duplicated/simplified logic and NO fabricated
fallback data: insufficient candles produce an honest `insufficient_data`
payload, never fake signals.
"""
from __future__ import annotations

import logging
from typing import Any

from app.indicators.atr import get_latest_atr
from app.indicators.rsi import get_latest_rsi
from app.indicators.volume import check_volume_confirmation
from app.models.candle import Candle
from app.strategy.level_detector import (
    LevelType,
    detect_fvg_3candles,
    evaluate_location_validity,
    find_support_resistance,
)
from app.strategy.momentum_filter import evaluate_15m_momentum
from app.strategy.pattern_detector import detect_1h_patterns, scan_series_patterns
from app.strategy.structure_analyzer import TrendDirection, analyze_4h_structure

logger = logging.getLogger("algotrade.market_analyzer")

MIN_LENGTH = 10

CRITERIA_KEYS = (
    "structure_4h",
    "location_valid",
    "pattern_1h",
    "momentum_15m",
    "rsi_confirmed",
    "volume_confirmed",
    "rr_valid",
    "stop_loss_valid",
)


class MarketAnalyzer:
    """Computes technical indicator values, SMC structures, and 8-criteria scores."""

    @staticmethod
    def analyze_candles(
        candles: list[Candle],
        symbol: str = "BTCUSDT",
        timeframe: str = "1h",
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform comprehensive 8-criteria evaluation via real strategy modules."""
        cfg = config or {}
        if "asset_class" not in cfg:
            if symbol and (symbol.endswith("USDT") or symbol.endswith("IRT") or "BTC" in symbol or "ETH" in symbol):
                cfg["asset_class"] = "crypto"
            else:
                cfg["asset_class"] = "forex"
                
        min_rr = float(cfg.get("min_risk_reward", 1.5))
        if not candles or len(candles) < MIN_LENGTH:
            return MarketAnalyzer._insufficient_data(symbol, timeframe)

        closes = [float(c.close) for c in candles]
        highs = [float(c.high) for c in candles]
        lows = [float(c.low) for c in candles]
        opens = [float(c.open) for c in candles]
        volumes = [float(c.volume) for c in candles]

        current_price = closes[-1]
        change_24h = float(round(((current_price - closes[0]) / max(closes[0], 1e-5)) * 100, 2))

        # ── Real stateless indicators (app/indicators) ──
        rsi_raw = get_latest_rsi(closes, 14)
        rsi = round(rsi_raw, 1) if rsi_raw == rsi_raw else 50.0  # NaN guard
        atr_raw = get_latest_atr(highs, lows, closes, 14)
        atr = atr_raw if atr_raw == atr_raw else max(highs[-1] - lows[-1], 1e-8)  # NaN guard
        vol_confirmed, vol_last, vol_ma10 = check_volume_confirmation(
            volumes, period=10, min_ratio=1.1
        )

        detected_patterns = scan_series_patterns(
            candles,
            symbol=symbol,
            timeframe=timeframe,
            config=cfg,
        )

        # Prioritize active pattern selection (exclude INVALIDATED and TARGET_HIT patterns):
        active_pat = None
        # 1. Live PRZ entry opportunity (zero-lag entry inside PRZ)
        for p in reversed(detected_patterns):
            if (
                p.get("is_developing")
                and not p.get("is_invalidated")
                and p.get("trade_setup")
                and p["trade_setup"].get("is_live_entry")
            ):
                active_pat = p
                break

        # 2. Confirmed 5-point Running Flat pattern with ACTIVE trade setup
        if not active_pat:
            for p in reversed(detected_patterns):
                if (
                    not p.get("is_developing")
                    and not p.get("is_invalidated")
                    and p.get("lifecycle_status", "ACTIVE") == "ACTIVE"
                    and p.get("trade_setup")
                    and p["trade_setup"].get("entry_price")
                ):
                    active_pat = p
                    break

        # 3. Any active developing wave (to show wave progression P0->P1->A->B->PRZ)
        if not active_pat:
            for p in reversed(detected_patterns):
                if p.get("is_developing") and not p.get("is_invalidated"):
                    active_pat = p
                    break

        is_pat_bull = (active_pat.get("direction") == "bullish") if active_pat else True
        has_executable_trade = bool(active_pat and active_pat.get("trade_setup") and active_pat["trade_setup"].get("entry_price"))
        trade_dir = "LONG" if is_pat_bull else "SHORT"

        # ── Real strategy engine modules (app/strategy) with pattern direction ──
        structure = analyze_4h_structure(highs, lows, closes)
        location = evaluate_location_validity(current_price, highs, lows, direction=trade_dir)
        pattern = detect_1h_patterns(opens, highs, lows, closes)
        momentum = evaluate_15m_momentum(closes, volumes, direction=trade_dir)

        # ── Real key levels (S/R clustering + 3-candle FVG) ──
        sr_levels = find_support_resistance(highs, lows)
        fvgs = detect_fvg_3candles(highs, lows)
        support = next((lvl for lvl in sr_levels if lvl.level_type == LevelType.SUPPORT), None)
        resistance = next((lvl for lvl in sr_levels if lvl.level_type == LevelType.RESISTANCE), None)
        bull_fvgs_below = [
            lvl for lvl in fvgs
            if lvl.level_type == LevelType.FVG_BULLISH and lvl.price_high <= current_price
        ]
        ob_demand = (
            bull_fvgs_below[-1].mid_price if bull_fvgs_below
            else (support.mid_price if support else current_price)
        )
        fvg_mid = fvgs[-1].mid_price if fvgs else (
            resistance.mid_price if resistance else current_price
        )
        sr_support = MarketAnalyzer._round_price(support.mid_price, current_price) if support else current_price
        sr_resistance = MarketAnalyzer._round_price(resistance.mid_price, current_price) if resistance else current_price

        # ── Structure-aware stop loss & risk/reward computation ──
        eff_atr = max(atr, current_price * 0.001)
        structure_stop = min(lows[-5:]) if len(lows) >= 5 else lows[-1]
        stop_loss_raw = min(current_price - 1.5 * eff_atr, structure_stop - 0.1 * eff_atr)
        stop_loss = MarketAnalyzer._round_price(stop_loss_raw, current_price)
        risk = max(current_price - stop_loss_raw, current_price * 0.0005)
        tp1 = MarketAnalyzer._round_price(current_price + 1.5 * risk, current_price)
        tp2 = MarketAnalyzer._round_price(current_price + 3.0 * risk, current_price)
        actual_rr = round((tp1 - current_price) / risk, 2) if risk > 0 else 0.0

        is_in_prz = bool(active_pat and active_pat.get("is_developing") and active_pat.get("trade_setup") and active_pat["trade_setup"].get("is_live_entry"))
        loc_valid = True if is_in_prz else bool(location.is_valid_location)
        mom_valid = True if is_in_prz else bool(momentum.is_confirmed)

        criteria = {
            "structure_4h": structure.direction == TrendDirection.BULLISH if is_pat_bull else structure.direction == TrendDirection.BEARISH,
            "location_valid": loc_valid,
            "pattern_1h": active_pat is not None,
            "momentum_15m": mom_valid,
            "rsi_confirmed": 35.0 <= rsi <= 75.0,
            "volume_confirmed": bool(vol_confirmed),
            "rr_valid": (active_pat["trade_setup"].get("risk_reward_ratio", 2.0) >= min_rr) if has_executable_trade else (actual_rr >= min_rr),
            "stop_loss_valid": (active_pat["trade_setup"].get("stop_loss", 0.0) > 0) if has_executable_trade else (stop_loss_raw < current_price),
        }

        score = sum(1 for v in criteria.values() if v)

        if has_executable_trade and active_pat:
            ts = active_pat["trade_setup"]
            raw_sig = ts.get("signal", "BUY" if is_pat_bull else "SELL")
            sig = raw_sig if score >= 6 else "WAIT"
            trade_setup = {
                "entry_price": MarketAnalyzer._round_price(ts["entry_price"], current_price),
                "stop_loss": MarketAnalyzer._round_price(ts["stop_loss"], current_price),
                "take_profit_1": MarketAnalyzer._round_price(ts["take_profit_1"], current_price),
                "take_profit_2": MarketAnalyzer._round_price(ts["take_profit_2"], current_price),
                "risk_reward_ratio": ts.get("risk_reward_ratio", 2.0),
                "signal": sig,
                "pattern_name": active_pat.get("name_en", "Running Flat"),
                "is_live_entry": bool(ts.get("is_live_entry", False)),
            }
        else:
            trade_setup = {
                "entry_price": MarketAnalyzer._round_price(current_price, current_price),
                "stop_loss": stop_loss,
                "take_profit_1": tp1,
                "take_profit_2": tp2,
                "risk_reward_ratio": actual_rr,
                "signal": "WAIT",
                "pattern_name": None,
                "is_live_entry": False,
            }

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "status": "ok",
            "pattern_probability": active_pat.get("pattern_probability", 0) if active_pat else 0,
            "trade_win_probability": active_pat.get("trade_win_probability", 0) if active_pat else 0,
            "progressive_stages": active_pat.get("progressive_stages", []) if active_pat else [],
            "is_developing": active_pat.get("is_developing", False) if active_pat else False,
            "stage": active_pat.get("stage", "") if active_pat else "",
            "stage_label": active_pat.get("stage_label", "") if active_pat else "",
            "current_price": MarketAnalyzer._round_price(current_price, current_price),
            "change_24h": change_24h,
            "score": score,
            "max_score": 8,
            "passed": score >= 6 and (active_pat is not None),
            "rsi": rsi,
            "atr": MarketAnalyzer._round_price(atr, current_price),
            "volume": round(vol_last, 2),
            "volume_ma10": round(vol_ma10, 2),
            "criteria": criteria,
            "details": {
                "structure": structure.description,
                "location": location.description,
                "pattern": f"الگوی {active_pat.get('name')}" if active_pat else "هیچ الگوی معتبری از AlefTrade یافت نشد",
                "momentum": momentum.description,
            },
            "detected_patterns": detected_patterns,
            "levels": {
                "order_block_demand": MarketAnalyzer._round_price(ob_demand, current_price),
                "fvg_imbalance": MarketAnalyzer._round_price(fvg_mid, current_price),
                "support_level": sr_support,
                "resistance_level": sr_resistance,
            },
            "trade_setup": trade_setup,
        }


    @staticmethod
    def _round_price(val: float, price_ref: float) -> float:
        """Dynamically round prices according to asset magnitude."""
        if price_ref < 0.001:
            return round(val, 8)
        elif price_ref < 0.1:
            return round(val, 6)
        elif price_ref < 10.0:
            return round(val, 5)
        elif price_ref < 500.0:
            return round(val, 3)
        return round(val, 2)

    @staticmethod
    def _insufficient_data(symbol: str, timeframe: str) -> dict[str, Any]:
        """
        HONEST empty analysis when there are not enough candles.

        NEVER fabricates prices, scores, or signals (the old fake fallback
        returned a hardcoded BTC price with score=7/BUY — removed).
        """
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "status": "insufficient_data",
            "current_price": 0.0,
            "change_24h": 0.0,
            "score": 0,
            "max_score": 8,
            "passed": False,
            "rsi": 50.0,
            "atr": 0.0,
            "volume": 0.0,
            "volume_ma10": 0.0,
            "criteria": {key: False for key in CRITERIA_KEYS},
            "details": {
                "structure": "",
                "location": "",
                "pattern": "",
                "momentum": "",
                "message": "تعداد کندل برای تحلیل کافی نیست. منتظر کندل‌های بیشتر بمانید.",
            },
            "detected_patterns": [],
            "levels": {
                "order_block_demand": 0.0,
                "fvg_imbalance": 0.0,
                "support_level": 0.0,
                "resistance_level": 0.0,
            },
            "trade_setup": {
                "entry_price": 0.0,
                "stop_loss": 0.0,
                "take_profit_1": 0.0,
                "take_profit_2": 0.0,
                "risk_reward_ratio": 0.0,
                "signal": "WAIT",
            },
        }
