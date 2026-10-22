# app/strategy/alef_markers.py
"""
Marker and trade setup builder for AlefTrade patterns.

Formats confirmed Elliott Wave patterns and real-time progressive wave stages
(WAVE_A_FORMED → WAVE_B_FORMING → WAVE_C_FORMING → PRZ_REVERSAL_TRIGGERED)
into structured payloads for Lightweight Charts and HUD cards.
"""
from __future__ import annotations

from typing import Any

from app.ml.pattern_recorder import compute_pattern_quality, get_pattern_recorder
from app.ml.wave_scorer import get_wave_scorer


def build_confirmed_marker(
    p: Any,
    timestamps: list[int],
    total_bars: int,
    df: Any | None = None,
) -> dict[str, Any]:
    """Format a confirmed Running Flat pattern into a detailed chart marker."""
    b0 = min(p.p0.bar_idx, total_bars - 1)
    b1 = min(p.p1.bar_idx, total_bars - 1)
    b2 = min(p.p2.bar_idx, total_bars - 1)
    b3 = min(p.p3.bar_idx, total_bars - 1)
    b4 = min(p.p4.bar_idx, total_bars - 1)

    is_bull = str(p.direction).lower().endswith("bullish")
    direction_str = "bullish" if is_bull else "bearish"
    marker_id = f"running_flat_{direction_str}_{b0}_{b4}"

    points = [
        {"label": "0", "name": "0 (شروع ایمپالس)", "price": round(p.p0.price, 5), "time": timestamps[b0], "bar_idx": b0},
        {"label": "1", "name": "1 (انتهای ایمپالس)", "price": round(p.p1.price, 5), "time": timestamps[b1], "bar_idx": b1},
        {"label": "A", "name": "A (موج A)", "price": round(p.p2.price, 5), "time": timestamps[b2], "bar_idx": b2},
        {"label": "B", "name": "B (موج B)", "price": round(p.p3.price, 5), "time": timestamps[b3], "bar_idx": b3},
        {"label": "C", "name": "C (موج C - ورود)", "price": round(p.p4.price, 5), "time": timestamps[b4], "bar_idx": b4},
    ]

    imp_len = abs(p.p1.price - p.p0.price)
    wa_len = abs(p.p1.price - p.p2.price)
    wb_len = abs(p.p3.price - p.p2.price)

    entry_p = p.trade_plan.entry_price if p.trade_plan else p.p4.price
    sl_p = p.trade_plan.stop_loss if p.trade_plan else (p.p2.price - wa_len * 0.15 if is_bull else p.p2.price + wa_len * 0.15)
    tp1_p = p.trade_plan.take_profit_1 if p.trade_plan else p.p3.price
    tp2_p = p.trade_plan.take_profit_2 if p.trade_plan else (entry_p + imp_len * 1.272 if is_bull else entry_p - imp_len * 1.272)
    rr_val = p.trade_plan.rr_ratio if p.trade_plan else round(abs(tp1_p - entry_p) / max(0.001, abs(entry_p - sl_p)), 2)

    # ── Deterministic Lifecycle Evaluation (Active, Invalidated upon P0 breach, or Target Hit) ──
    lifecycle_status = "ACTIVE"
    is_invalidated = False
    is_target_hit = False
    invalidation_reason = None

    if df is not None and b4 < len(df) - 1:
        for idx in range(b4 + 1, len(df)):
            row = df.iloc[idx]
            c_high = float(row["high"])
            c_low = float(row["low"])
            if is_bull:
                if c_low < p.p0.price:
                    lifecycle_status = "INVALIDATED"
                    is_invalidated = True
                    invalidation_reason = f"نفوذ قیمت به زیر تراز کف P0 ({p.p0.price:.2f})"
                    break
                elif c_high >= tp1_p:
                    lifecycle_status = "TARGET_HIT"
                    is_target_hit = True
                    break
            else:
                if c_high > p.p0.price:
                    lifecycle_status = "INVALIDATED"
                    is_invalidated = True
                    invalidation_reason = f"نفوذ قیمت به بالای تراز سقف P0 ({p.p0.price:.2f})"
                    break
                elif c_low <= tp1_p:
                    lifecycle_status = "TARGET_HIT"
                    is_target_hit = True
                    break

    if lifecycle_status == "INVALIDATED":
        pat_color = "#64748b"  # Muted slate gray
        status_suffix = " [✕ باطل شده]"
        stage_lbl = f"باطل شده - نفوذ به تراز P0 ({p.p0.price:.2f})"
    elif lifecycle_status == "TARGET_HIT":
        pat_color = "#10b981"  # Vibrant emerald
        status_suffix = " [🎯 تارگت ۱]"
        stage_lbl = "موفق - تارگت اول محقق شد 🎯"
    else:
        pat_color = "#3b82f6" if is_bull else "#ef4444"
        status_suffix = " [⚡ فعال]"
        stage_lbl = "الگوی کامل تایید شد - ستاپ فعال ⚡"

    trade_setup = {
        "entry": round(entry_p, 5),
        "entry_price": round(entry_p, 5),
        "stop_loss": round(sl_p, 5),
        "take_profit_1": round(tp1_p, 5),
        "take_profit_2": round(tp2_p, 5),
        "risk_reward_ratio": rr_val,
        "signal": ("BUY" if is_bull else "SELL") if lifecycle_status == "ACTIVE" else "WAIT",
        "is_live_entry": False,
        "lifecycle_status": lifecycle_status,
        "is_invalidated": is_invalidated,
        "is_target_hit": is_target_hit,
        "invalidation_reason": invalidation_reason,
    }

    pat_prob, win_prob, ml_engine = get_wave_scorer().score_pattern(
        p, rr_val=rr_val, is_invalidated=is_invalidated, is_target_hit=is_target_hit
    )
    qg = compute_pattern_quality(
        retr_a=p.retr_a, retr_b=p.retr_b, retr_c=p.retr_c,
        slope_ratio=p.slope_ratio, er_b=p.er_b, dtw_score=p.dtw_score,
        rr_ratio=rr_val,
    )

    prz_top = p.p3.price - (wb_len * 0.60) if is_bull else p.p3.price + (wb_len * 0.60)
    prz_bot = max(p.p2.price, p.p3.price - (wb_len * 1.05)) if is_bull else min(p.p2.price, p.p3.price + (wb_len * 1.05))

    rules_eval = [
        {"rule": "موج A (اصلاح ۰.۱۵ تا ۰.۸۰)", "passed": True, "value": f"{p.retr_a*100:.1f}%"},
        {"rule": "موج B (انبساط ۱.۰۲ تا ۲.۵۰)", "passed": True, "value": f"{p.retr_b*100:.1f}%"},
        {"rule": "موج C (بازگشت ۰.۶۰ تا ۱.۰۵)", "passed": True, "value": f"{p.retr_c*100:.1f}%"},
        {"rule": "نسبت شیب زمانی (Slope Ratio >= 1.0)", "passed": True, "value": f"{p.slope_ratio:.2f}"},
        {"rule": "شاخص کارایی (Kaufman ER <= 0.40)", "passed": True, "value": f"{p.er_b:.2f}"},
    ]

    progressive_stages = [
        {"step": 1, "name": "ایمپالس اولیه (P0 → P1)", "status": "COMPLETED", "detail": f"طول ایمپالس: {imp_len:.2f}", "passed": True},
        {"step": 2, "name": "اصلاح موج A (P1 → P2)", "status": "COMPLETED", "detail": f"نسبت اصلاح: {p.retr_a*100:.1f}%", "passed": True},
        {"step": 3, "name": "شکست و انبساط موج B (P2 → P3)", "status": "COMPLETED", "detail": f"نسبت انبساط: {p.retr_b*100:.1f}%", "passed": True},
        {"step": 4, "name": "محدوده شکار و بازگشت (PRZ)", "status": "COMPLETED", "detail": f"باکس ۰.۶۰ تا ۱.۰۵ (نفوذ: {p.retr_c*100:.1f}%)", "passed": True},
        {"step": 5, "name": "تایید نهایی و تریگر ورود (نقطه C)", "status": "COMPLETED", "detail": f"ورود در قیمت {p.p4.price:.2f} با R:R {rr_val}x", "passed": True},
    ]
    if lifecycle_status == "INVALIDATED":
        progressive_stages.append({
            "step": 6, "name": "نقض تراز ساختار P0", "status": "FAILED",
            "detail": f"نقض قطعی تراز P0 در قیمت {p.p0.price:.2f} (خروج اضطراری)", "passed": False,
        })
    elif lifecycle_status == "TARGET_HIT":
        progressive_stages.append({
            "step": 6, "name": "تحقق تارگت سود", "status": "COMPLETED",
            "detail": f"تارگت اول در قیمت {tp1_p:.2f} با موفقیت لمس شد", "passed": True,
        })

    res = {
        "id": marker_id,
        "category": "flat",
        "type": "running_flat",
        "name": f"الگوی رانینگ فلت ({'صعودی' if is_bull else 'نزولی'}){status_suffix}",
        "name_en": f"Running Flat ({'Bullish' if is_bull else 'Bearish'})",
        "direction": direction_str,
        "time": timestamps[b4],
        "price": round(p.p4.price, 5),
        "pattern_color": pat_color,
        "stage": lifecycle_status,
        "stage_label": stage_lbl,
        "lifecycle_status": lifecycle_status,
        "is_invalidated": is_invalidated,
        "is_target_hit": is_target_hit,
        "invalidation_reason": invalidation_reason,
        "pattern_probability": pat_prob,
        "trade_win_probability": win_prob,
        "ml_engine": ml_engine,
        "quality_score": qg.score,
        "quality_grade": qg.grade,
        "grade_color": qg.grade_color,
        "quality_strengths": qg.strengths,
        "quality_cautions": qg.cautions,
        "progressive_stages": progressive_stages,
        "points": points,
        "trade_setup": trade_setup,
        "rules_evaluation": rules_eval,
        "prz_zone": {
            "top": max(prz_top, prz_bot),
            "bottom": min(prz_top, prz_bot),
            "start_time": timestamps[b2],
            "end_time": timestamps[b4],
            "label": f"PRZ [{'باطل شده' if is_invalidated else ('موفق' if is_target_hit else 'فعال')}]",
        },
        "details": {
            "retr_a": round(p.retr_a, 4), "retr_b": round(p.retr_b, 4),
            "retr_c": round(p.retr_c, 4), "slope_ratio": round(p.slope_ratio, 2),
            "er_b": round(p.er_b, 4), "chop_b": round(p.chop_b, 2), "dtw_score": round(p.dtw_score, 4),
        },
    }
    try:
        get_pattern_recorder().record_pattern(res, symbol="CHART", timeframe="1h")
    except Exception:
        pass
    return res


def build_developing_marker(
    dev: Any,
    timestamps: list[int],
    total_bars: int,
) -> dict[str, Any]:
    """Format a progressive developing wave into an instant real-time chart marker."""
    st_bar = min(dev.p2.bar_idx if dev.p2 else 0, total_bars - 1)
    cur_bar = min(dev.cur_ext_bar, total_bars - 1)
    is_bull = str(dev.direction).lower().endswith("bullish")
    prz_high = max(dev.prz_top, dev.prz_bottom) if dev.prz_top > 0 else 0.0
    prz_low = min(dev.prz_top, dev.prz_bottom) if dev.prz_bottom > 0 else 0.0

    dev_points = []
    if dev.p0 and dev.p1 and dev.p2:
        dev_b0 = min(dev.p0.bar_idx, total_bars - 1)
        dev_b1 = min(dev.p1.bar_idx, total_bars - 1)
        dev_b2 = min(dev.p2.bar_idx, total_bars - 1)
        dev_points = [
            {"label": "0", "name": "0 (شروع ایمپالس)", "price": round(dev.p0.price, 5), "time": timestamps[dev_b0], "bar_idx": dev_b0},
            {"label": "1", "name": "1 (انتهای ایمپالس)", "price": round(dev.p1.price, 5), "time": timestamps[dev_b1], "bar_idx": dev_b1},
            {"label": "A", "name": "A (موج A)", "price": round(dev.p2.price, 5), "time": timestamps[dev_b2], "bar_idx": dev_b2},
        ]
        if dev.p3:
            dev_b3 = min(dev.p3.bar_idx, total_bars - 1)
            dev_points.append({"label": "B", "name": "B (موج B)", "price": round(dev.p3.price, 5), "time": timestamps[dev_b3], "bar_idx": dev_b3})

    if dev.stage == "WAVE_B_FORMING":
        dev_points.append({
            "label": "B", "name": "B (در حال شکست و انبساط)",
            "price": round(dev.cur_ext_price, 5), "time": timestamps[cur_bar], "bar_idx": cur_bar, "is_developing": True,
        })
    elif dev.stage in ["WAVE_C_FORMING", "PRZ_REVERSAL_ZONE", "PRZ_REVERSAL_TRIGGERED"] and dev.cur_ext_price > 0:
        c_lbl = "C (ورود قطعی در PRZ)" if dev.stage == "PRZ_REVERSAL_TRIGGERED" else "C (در حال تشکیل در PRZ)"
        dev_points.append({
            "label": "C", "name": c_lbl,
            "price": round(dev.cur_ext_price, 5), "time": timestamps[cur_bar], "bar_idx": cur_bar, "is_developing": True,
        })

    imp_l = abs(dev.p1.price - dev.p0.price) if (dev.p1 and dev.p0) else 1.0
    wa_l = abs(dev.p1.price - dev.p2.price) if (dev.p1 and dev.p2) else 1.0
    wb_l = abs(dev.p3.price - dev.p2.price) if (dev.p3 and dev.p2) else wa_l
    r_a = wa_l / imp_l if imp_l > 0 else 0.0
    cur_retr = dev.current_retr

    is_wave_a = dev.stage == "WAVE_A_FORMED"
    is_wave_b = dev.stage == "WAVE_B_FORMING"
    is_wave_c = dev.stage == "WAVE_C_FORMING"
    in_prz = dev.stage in ["PRZ_REVERSAL_ZONE", "PRZ_REVERSAL_TRIGGERED"]
    is_triggered = dev.stage == "PRZ_REVERSAL_TRIGGERED"

    if is_wave_a:
        pat_prob = 52
        win_prob = 48
        stage_lbl = "ایمپالس و موج A تشکیل شد؛ در انتظار انبساط موج B"
    elif is_wave_b:
        pat_prob = min(68, max(45, int(40 + min(cur_retr, 1.5) * 18)))
        win_prob = 52
        stage_lbl = f"انبساط موج B ({cur_retr*100:.1f}%)"
    elif is_triggered:
        pat_prob = min(96, max(88, int(90 + (1.0 - abs(cur_retr - 0.786)) * 12)))
        win_prob = 82
        stage_lbl = "سیگنال زنده ورود در PRZ فعال شد ⚡"
    elif in_prz:
        pat_prob = min(92, max(78, int(75 + (1.0 - abs(cur_retr - 0.786)) * 20)))
        stage_lbl = "شکار ورود در محدوده PRZ"
        win_prob = 75
    elif is_wave_c:
        pat_prob = min(75, max(50, int(45 + cur_retr * 40)))
        stage_lbl = f"حرکت به سمت PRZ ({cur_retr*100:.1f}%)"
        win_prob = 58
    else:
        pat_prob = 40
        stage_lbl = dev.status_text
        win_prob = 45

    dev_trade_setup: dict[str, Any] = {}
    entry_p = round(dev.cur_ext_price, 5)
    sl_p = round(dev.p2.price - (wa_l * 0.15) if is_bull else dev.p2.price + (wa_l * 0.15), 5)
    tp1_p = round(dev.p3.price if dev.p3 else dev.p1.price, 5)
    tp2_p = round(entry_p + (imp_l * 1.272) if is_bull else entry_p - (imp_l * 1.272), 5)
    risk_pts = abs(entry_p - sl_p)
    reward_pts = abs(tp1_p - entry_p)
    rr_ratio = round((reward_pts / risk_pts), 2) if risk_pts > 0 else 1.5

    if in_prz:
        dev_trade_setup = {
            "entry": entry_p,
            "entry_price": entry_p,
            "stop_loss": sl_p,
            "take_profit_1": tp1_p,
            "take_profit_2": tp2_p,
            "risk_reward_ratio": rr_ratio,
            "signal": "BUY" if is_bull else "SELL",
            "is_live_entry": True,
        }
        win_prob = min(90, max(70, int(65 + min(rr_ratio, 4.0) * 6.5)))

    progressive_stages = [
        {"step": 1, "name": "ایمپالس اولیه (P0 → P1)", "status": "COMPLETED", "detail": f"طول ایمپالس: {imp_l:.2f}", "passed": True},
        {"step": 2, "name": "اصلاح موج A (P1 → P2)", "status": "COMPLETED", "detail": f"نسبت اصلاح: {r_a*100:.1f}%", "passed": True},
        {
            "step": 3,
            "name": "شکست و انبساط موج B (P2 → P3)",
            "status": "COMPLETED" if (is_wave_c or in_prz) else ("ACTIVE" if is_wave_b else "WAITING"),
            "detail": f"شکست P1 تایید شد ({cur_retr*100:.1f}%)" if (is_wave_b or is_wave_c or in_prz) else "در انتظار شکست سطح P1",
            "passed": is_wave_b or is_wave_c or in_prz,
        },
        {
            "step": 4,
            "name": "محدوده شکار و بازگشت (PRZ)",
            "status": "COMPLETED" if is_triggered else ("ACTIVE" if in_prz else ("WAITING" if is_wave_c else "PENDING")),
            "detail": f"باکس ۰.۶۰ تا ۱.۰۵ (نفوذ: {cur_retr*100:.1f}%)" if (is_wave_c or in_prz) else "در انتظار تکمیل موج B",
            "passed": in_prz,
        },
        {
            "step": 5,
            "name": "تایید نهایی و تریگر ورود (نقطه C)",
            "status": "COMPLETED" if is_triggered else ("READY_TO_TRIGGER" if in_prz else "PENDING"),
            "detail": f"سیگنال زنده ورود در {entry_p} با R:R {rr_ratio}x ⚡" if in_prz else "در انتظار ورود به PRZ",
            "passed": in_prz,
        },
    ]

    return {
        "id": f"developing_prz_{'bull' if is_bull else 'bear'}_{cur_bar}",
        "category": "flat",
        "type": "running_flat",
        "name": f"منطقه شکار معامله (PRZ) - رانینگ فلت {'صعودی' if is_bull else 'نزولی'}",
        "name_en": f"PRZ Reversal Zone - Running Flat ({'Bullish' if is_bull else 'Bearish'})",
        "direction": "bullish" if is_bull else "bearish",
        "time": timestamps[cur_bar],
        "price": round(dev.cur_ext_price, 5),
        "pattern_color": "#10b981" if (is_triggered and is_bull) else ("#ef4444" if is_triggered else "#f59e0b"),
        "is_developing": True,
        "lifecycle_status": "ACTIVE",
        "is_invalidated": False,
        "is_target_hit": False,
        "status_text": dev.status_text,
        "stage": dev.stage,
        "stage_label": stage_lbl,
        "pattern_probability": pat_prob,
        "trade_win_probability": win_prob,
        "progressive_stages": progressive_stages,
        "points": dev_points,
        "trade_setup": dev_trade_setup,
        "prz_zone": {
            "top": round(prz_high, 5), "bottom": round(prz_low, 5),
            "start_time": timestamps[st_bar], "end_time": timestamps[cur_bar],
            "label": f"PRZ ({dev.stage})",
        },
    }
