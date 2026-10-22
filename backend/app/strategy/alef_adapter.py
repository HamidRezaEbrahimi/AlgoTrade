# app/strategy/alef_adapter.py
"""
AlefTrade Adapter for AlgoTrade.

Bridges the high-precision Elliott Wave & pattern engine from AlefTrade
into AlgoTrade's market analysis pipeline and frontend TradingView charts.
Implements multi-scale noise filtering, progressive wave tracking
(P0→P1→A→B→PRZ→C), and zero-lag predictive trade execution inside PRZ.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import pandas as pd

from app.models.candle import Candle
from app.strategy.alef_markers import build_confirmed_marker, build_developing_marker

logger = logging.getLogger("algotrade.strategy.alef_adapter")


def _scan_progressive_wave_action(
    df: pd.DataFrame,
    pivots: list[Any],
    rf_config: Any,
) -> Any | None:
    """Detect candle-by-candle progressive wave formation and zero-lag PRZ trigger."""
    try:
        from AlefTrade import DevelopingWave, PatternDirection, PivotPoint, PivotType
    except ImportError:
        return None

    if len(pivots) < 3 or len(df) < 5:
        return None

    cur_bar = len(df) - 1
    cur_close = float(df["close"].iloc[-1])
    cur_open = float(df["open"].iloc[-1])

    # Scan from the most recent pivots backwards to find the latest valid P0, P1, A
    for i in range(len(pivots) - 1, 1, -1):
        cand_p0 = pivots[i - 2]
        cand_p1 = pivots[i - 1]
        cand_p2 = pivots[i]

        # ── Case A: Bearish Running Flat Setup (P0 High -> P1 Low -> P2 High A) ──
        if (
            cand_p0.p_type == PivotType.HIGH
            and cand_p1.p_type == PivotType.LOW
            and cand_p2.p_type == PivotType.HIGH
        ):
            imp_l = cand_p0.price - cand_p1.price
            wa_l = cand_p2.price - cand_p1.price
            if imp_l <= 0 or not (rf_config.min_retr_a <= (wa_l / imp_l) <= rf_config.max_retr_a):
                continue
            # Invalidation guard: Bearish wave invalid if price exceeds P0 ceiling
            if float(df.iloc[cand_p0.bar_idx:]["high"].max()) > cand_p0.price:
                continue

            a_bar = cand_p2.bar_idx
            df_since_a = df.iloc[a_bar:]
            min_low_val = float(df_since_a["low"].min())
            min_low_idx = int(df_since_a["low"].idxmin())
            wb_l = cand_p2.price - min_low_val
            r_b = wb_l / wa_l if wa_l > 0 else 0.0

            # Stage 2: Wave A formed, price before breaking P1
            if min_low_val >= cand_p1.price or r_b < rf_config.min_retr_b:
                return DevelopingWave(
                    stage="WAVE_A_FORMED",
                    direction=PatternDirection.BEARISH,
                    p0=cand_p0, p1=cand_p1, p2=cand_p2,
                    cur_ext_bar=a_bar,
                    cur_ext_price=cand_p2.price,
                    prz_top=0.0, prz_bottom=0.0, current_retr=wa_l / imp_l,
                    status_text=f"ایمپالس و موج A تشکیل شد ({(wa_l/imp_l)*100:.1f}%)؛ در انتظار شکست P1",
                    is_invalidated=False,
                )

            # Stage 3 to 5: Wave B broke P1
            if rf_config.min_retr_b <= r_b <= rf_config.max_retr_b:
                prz_b = min_low_val + (wb_l * rf_config.min_retr_c)
                prz_t = min(cand_p2.price, min_low_val + (wb_l * rf_config.max_retr_c))

                df_since_b = df.iloc[min_low_idx:]
                max_high_val = float(df_since_b["high"].max())
                max_high_idx = int(df_since_b["high"].idxmax())
                wc_l = max_high_val - min_low_val
                r_c = wc_l / wb_l if wb_l > 0 else 0.0
                t_b = int(df["timestamp"].iloc[min_low_idx]) if "timestamp" in df.columns else None
                p_b = PivotPoint(min_low_idx, min_low_val, PivotType.LOW, timestamp=t_b)

                # Wave B still extending or Wave C just starting
                if max_high_val <= min_low_val + 0.3:
                    return DevelopingWave(
                        stage="WAVE_B_FORMING",
                        direction=PatternDirection.BEARISH,
                        p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b,
                        cur_ext_bar=min_low_idx,
                        cur_ext_price=min_low_val,
                        prz_top=prz_t, prz_bottom=prz_b, current_retr=r_b,
                        status_text=f"موج B در حال شکست P1 ({r_b*100:.1f}%)",
                        is_invalidated=False,
                    )

                # Wave C moving towards PRZ
                if r_c < rf_config.min_retr_c:
                    return DevelopingWave(
                        stage="WAVE_C_FORMING",
                        direction=PatternDirection.BEARISH,
                        p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b,
                        cur_ext_bar=max_high_idx,
                        cur_ext_price=max_high_val,
                        prz_top=prz_t, prz_bottom=prz_b, current_retr=r_c,
                        status_text=f"موج C در حال حرکت به سمت PRZ ({r_c*100:.1f}%)",
                        is_invalidated=False,
                    )

                # Wave C inside PRZ (Zero-Lag Reversal Detection)
                if rf_config.min_retr_c <= r_c <= rf_config.max_retr_c:
                    is_reversal = (cur_close < max_high_val - 0.2) or (cur_close < cur_open) or (max_high_idx < cur_bar)
                    stage_name = "PRZ_REVERSAL_TRIGGERED" if is_reversal else "PRZ_REVERSAL_ZONE"
                    return DevelopingWave(
                        stage=stage_name,
                        direction=PatternDirection.BEARISH,
                        p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b,
                        cur_ext_bar=max_high_idx,
                        cur_ext_price=max_high_val,
                        prz_top=prz_t, prz_bottom=prz_b, current_retr=r_c,
                        status_text="سیگنال ورود قطعی در PRZ فعال شد ⚡" if is_reversal else f"موج C در محدوده شکار PRZ ({r_c*100:.1f}%)",
                        is_invalidated=False,
                    )

        # ── Case B: Bullish Running Flat Setup (P0 Low -> P1 High -> P2 Low A) ──
        elif (
            cand_p0.p_type == PivotType.LOW
            and cand_p1.p_type == PivotType.HIGH
            and cand_p2.p_type == PivotType.LOW
        ):
            imp_l = cand_p1.price - cand_p0.price
            wa_l = cand_p1.price - cand_p2.price
            if imp_l <= 0 or not (rf_config.min_retr_a <= (wa_l / imp_l) <= rf_config.max_retr_a):
                continue
            # Invalidation guard: Bullish wave invalid if price drops below P0 floor
            if float(df.iloc[cand_p0.bar_idx:]["low"].min()) < cand_p0.price:
                continue

            a_bar = cand_p2.bar_idx
            df_since_a = df.iloc[a_bar:]
            max_high_val = float(df_since_a["high"].max())
            max_high_idx = int(df_since_a["high"].idxmax())
            wb_l = max_high_val - cand_p2.price
            r_b = wb_l / wa_l if wa_l > 0 else 0.0

            if max_high_val <= cand_p1.price or r_b < rf_config.min_retr_b:
                return DevelopingWave(
                    stage="WAVE_A_FORMED",
                    direction=PatternDirection.BULLISH,
                    p0=cand_p0, p1=cand_p1, p2=cand_p2,
                    cur_ext_bar=a_bar,
                    cur_ext_price=cand_p2.price,
                    prz_top=0.0, prz_bottom=0.0, current_retr=wa_l / imp_l,
                    status_text=f"ایمپالس و موج A تشکیل شد ({(wa_l/imp_l)*100:.1f}%)؛ در انتظار شکست P1",
                    is_invalidated=False,
                )

            if rf_config.min_retr_b <= r_b <= rf_config.max_retr_b:
                prz_t = max_high_val - (wb_l * rf_config.min_retr_c)
                prz_b = max(cand_p2.price, max_high_val - (wb_l * rf_config.max_retr_c))

                df_since_b = df.iloc[max_high_idx:]
                min_low_val = float(df_since_b["low"].min())
                min_low_idx = int(df_since_b["low"].idxmin())
                wc_l = max_high_val - min_low_val
                r_c = wc_l / wb_l if wb_l > 0 else 0.0
                t_b = int(df["timestamp"].iloc[max_high_idx]) if "timestamp" in df.columns else None
                p_b = PivotPoint(max_high_idx, max_high_val, PivotType.HIGH, timestamp=t_b)

                if min_low_val >= max_high_val - 0.3:
                    return DevelopingWave(
                        stage="WAVE_B_FORMING",
                        direction=PatternDirection.BULLISH,
                        p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b,
                        cur_ext_bar=max_high_idx,
                        cur_ext_price=max_high_val,
                        prz_top=prz_t, prz_bottom=prz_b, current_retr=r_b,
                        status_text=f"موج B در حال شکست P1 ({r_b*100:.1f}%)",
                        is_invalidated=False,
                    )

                if r_c < rf_config.min_retr_c:
                    return DevelopingWave(
                        stage="WAVE_C_FORMING",
                        direction=PatternDirection.BULLISH,
                        p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b,
                        cur_ext_bar=min_low_idx,
                        cur_ext_price=min_low_val,
                        prz_top=prz_t, prz_bottom=prz_b, current_retr=r_c,
                        status_text=f"موج C در حال حرکت به سمت PRZ ({r_c*100:.1f}%)",
                        is_invalidated=False,
                    )

                if rf_config.min_retr_c <= r_c <= rf_config.max_retr_c:
                    is_reversal = (cur_close > min_low_val + 0.2) or (cur_close > cur_open) or (min_low_idx < cur_bar)
                    stage_name = "PRZ_REVERSAL_TRIGGERED" if is_reversal else "PRZ_REVERSAL_ZONE"
                    return DevelopingWave(
                        stage=stage_name,
                        direction=PatternDirection.BULLISH,
                        p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b,
                        cur_ext_bar=min_low_idx,
                        cur_ext_price=min_low_val,
                        prz_top=prz_t, prz_bottom=prz_b, current_retr=r_c,
                        status_text="سیگنال ورود قطعی در PRZ فعال شد ⚡" if is_reversal else f"موج C در محدوده شکار PRZ ({r_c*100:.1f}%)",
                        is_invalidated=False,
                    )
    return None


def scan_patterns_with_alef(
    candles: Sequence[Candle],
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Execute AlefTrade engine with multi-scale filtering and zero-lag PRZ tracking."""
    if len(candles) < 20:
        return []

    try:
        from AlefTrade import (
            AdaptiveZigZag,
            PatternType,
            RunningFlatConfig,
            RunningFlatDetector,
            ZigZagConfig,
        )
    except ImportError as e:
        logger.error("AlefTrade package not installed: %s", e)
        return []

    df = pd.DataFrame([
        {
            "time": int(c.timestamp.timestamp()),
            "timestamp": int(c.timestamp.timestamp()),
            "open": float(c.open),
            "high": float(c.high),
            "low": float(c.low),
            "close": float(c.close),
            "volume": float(c.volume),
        }
        for c in candles
    ])
    timestamps = [int(c.timestamp.timestamp()) for c in candles]
    total_bars = len(candles)
    from app.strategy.alef_config import load_alef_trade_config

    alef_settings = load_alef_trade_config()
    rf_saved = alef_settings.get("running_flat", {})
    cfg = {**rf_saved, **(config or {})}
    rf_config = RunningFlatConfig(
        min_retr_a=float(cfg.get("min_retr_a", 0.15)),
        max_retr_a=float(cfg.get("max_retr_a", 0.85)),
        min_retr_b=float(cfg.get("min_retr_b", 1.02)),
        max_retr_b=float(cfg.get("max_retr_b", 2.50)),
        min_retr_c=float(cfg.get("min_retr_c", 0.60)),
        max_retr_c=float(cfg.get("max_retr_c", 1.05)),
        min_slope_ratio=float(cfg.get("min_slope_ratio", 1.00)),
        enable_er_filter=bool(cfg.get("enable_er_filter", False)),
        enable_chop=bool(cfg.get("enable_chop", False)),
        use_trend_filter=bool(cfg.get("use_trend_filter", False)),
    )

    tf_str = str(timeframe).lower().strip()
    is_scalp = tf_str in ["1m", "3m", "5m", "1", "3", "5"]
    mult_macro = float(cfg.get("atr_mult_macro", 3.5 if is_scalp else 2.6))
    mult_base = float(cfg.get("atr_mult_base", 2.0 if is_scalp else 1.8))

    detector = RunningFlatDetector(config=rf_config)

    zz_macro = AdaptiveZigZag(config=ZigZagConfig(atr_multiplier=mult_macro, auto_timeframe_mult=False))
    pivots_macro = zz_macro.calculate(df, timeframe=timeframe)
    pats_macro = detector.detect(df, pivots_macro, timeframe=timeframe)

    zz_base = AdaptiveZigZag(config=ZigZagConfig(atr_multiplier=mult_base, auto_timeframe_mult=False))
    pivots_base = zz_base.calculate(df, timeframe=timeframe)
    pats_base = detector.detect(df, pivots_base, timeframe=timeframe)

    macro_ranges = [(p.p0.bar_idx, p.p4.bar_idx) for p in pats_macro]
    clean_base = [
        p for p in pats_base
        if not any(m_st <= p.p0.bar_idx and p.p4.bar_idx <= m_end for m_st, m_end in macro_ranges)
    ]
    confirmed_patterns = list(pats_macro) + clean_base
    confirmed_patterns.sort(key=lambda p: (p.p4.bar_idx, abs(p.p1.price - p.p0.price)))

    markers: list[dict[str, Any]] = [
        build_confirmed_marker(p, timestamps, total_bars, df=df)
        for p in confirmed_patterns
        if p.pattern_type == PatternType.RUNNING_FLAT
    ]

    # Live progressive wave tracking directly via AlefTrade native engine
    if hasattr(detector, "scan_progressive_developing"):
        prog_wave = detector.scan_progressive_developing(df, pivots_macro, timeframe=timeframe)
    else:
        prog_wave = _scan_progressive_wave_action(df, pivots_macro, rf_config)
    if prog_wave:
        markers.append(build_developing_marker(prog_wave, timestamps, total_bars))

    return markers
