# app/strategy/patterns/trade_zones.py
"""
Per-Pattern Trade Zone Calculator.

Computes pattern-specific Entry Zones (A/B), Stop Loss, and Take Profit
levels based on the geometric properties of each detected wave pattern.

Each pattern type has its own trading logic:
- Flag: Entry on C-wave trendline break, SL below P4/P0, TP = measured move
- Regular Flat: Entry near P4 (C completion at P2 level), SL below P4
- Expanded Flat: Entry after liquidity sweep reversal, SL at C extreme
- Running Flat: Entry at shallow P4, SL below P2
- Contract/Complex Flat: Entry on range breakout, SL at opposite extreme
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TradeZone:
    """A single trade level with price, label, and metadata."""

    price: float
    label_fa: str
    label_en: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "price": round(self.price, 8),
            "label": self.label_fa,
            "label_en": self.label_en,
        }


@dataclass
class PatternTradeZones:
    """Complete trade setup for a detected pattern."""

    entry_a: TradeZone  # Aggressive entry (earlier, higher risk)
    entry_b: TradeZone  # Conservative entry (later, lower risk)
    stop_loss: TradeZone
    tp1: TradeZone  # First take profit (measured move)
    tp2: TradeZone  # Extended take profit (1.618 extension)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_a": self.entry_a.to_dict(),
            "entry_b": self.entry_b.to_dict(),
            "stop_loss": self.stop_loss.to_dict(),
            "tp1": self.tp1.to_dict(),
            "tp2": self.tp2.to_dict(),
        }


def calculate_trade_zones(
    cycle: dict[str, Any],
    category: str,
    atr: float,
) -> PatternTradeZones:
    """
    Calculate pattern-specific trade zones.

    Args:
        cycle: Wave cycle dict with p0-p5 prices and geometry.
        category: Pattern category key (flag, regular_flat, expanded_flat, etc).
        atr: Current Average True Range for buffer calculations.

    Returns:
        PatternTradeZones with Entry A/B, SL, TP1, TP2.
    """
    is_bull = cycle["direction"] == "bullish"
    sign = 1.0 if is_bull else -1.0

    p0 = cycle["p0_price"]
    p1 = cycle["p1_price"]
    p2 = cycle["p2_price"]
    p3 = cycle["p3_price"]
    p4 = cycle["p4_price"]
    disp = cycle["disp"]  # Impulse 1 displacement

    calculator = _ZONE_CALCULATORS.get(category, _calc_default_zones)
    return calculator(
        p0=p0, p1=p1, p2=p2, p3=p3, p4=p4,
        disp=disp, atr=atr, is_bull=is_bull, sign=sign,
    )


# ─────────────────────────────────────────────────
# Per-pattern zone calculators
# ─────────────────────────────────────────────────

def _calc_flag_zones(
    *, p0: float, p1: float, p2: float, p3: float, p4: float,
    disp: float, atr: float, is_bull: bool, sign: float,
) -> PatternTradeZones:
    """
    Flag pattern trade zones.

    Entry A: Near P2 (aggressive, early in the correction).
    Entry B: Near P4 (conservative, after C-wave completes).
    SL: Beyond P4 with ATR buffer (tight) or beyond P0 (wide/safe).
    TP1: Measured move (100% of impulse from P4).
    TP2: Extended measured move (161.8% of impulse from P4).
    """
    sl_tight = p4 - sign * 0.5 * atr  # Tight SL: just beyond P4
    tp1 = p4 + sign * disp  # 100% measured move
    tp2 = p4 + sign * 1.618 * disp  # 161.8% extension

    return PatternTradeZones(
        entry_a=TradeZone(
            price=p2,
            label_fa="ورود A (نزدیک P2 - تهاجمی)",
            label_en="Entry A (near P2 - aggressive)",
        ),
        entry_b=TradeZone(
            price=p4,
            label_fa="ورود B (نزدیک P4 - محافظه‌کارانه)",
            label_en="Entry B (near P4 - conservative)",
        ),
        stop_loss=TradeZone(
            price=sl_tight,
            label_fa="حد ضرر (زیر P4)",
            label_en="Stop Loss (below P4)",
        ),
        tp1=TradeZone(
            price=tp1,
            label_fa="تارگت ۱ (اندازه ایمپالس ۱۰۰٪)",
            label_en="TP1 (100% measured move)",
        ),
        tp2=TradeZone(
            price=tp2,
            label_fa="تارگت ۲ (اکستنشن ۱۶۱.۸٪)",
            label_en="TP2 (161.8% extension)",
        ),
    )


def _calc_regular_flat_zones(
    *, p0: float, p1: float, p2: float, p3: float, p4: float,
    disp: float, atr: float, is_bull: bool, sign: float,
) -> PatternTradeZones:
    """
    Regular Flat: C ends near A (P4 ≈ P2).

    Entry A: Near P2 (anticipating C completion at same level).
    Entry B: At P4 after reversal confirmation.
    SL: Beyond P4 with buffer.
    """
    sl = p4 - sign * atr  # Buffer beyond P4
    tp1 = p4 + sign * disp
    tp2 = p4 + sign * 1.618 * disp

    return PatternTradeZones(
        entry_a=TradeZone(
            price=p2,
            label_fa="ورود A (سطح موج A - تهاجمی)",
            label_en="Entry A (wave A level - aggressive)",
        ),
        entry_b=TradeZone(
            price=p4,
            label_fa="ورود B (تکمیل موج C)",
            label_en="Entry B (C-wave completion)",
        ),
        stop_loss=TradeZone(
            price=sl,
            label_fa="حد ضرر (فراتر از P4 + بافر ATR)",
            label_en="SL (beyond P4 + ATR buffer)",
        ),
        tp1=TradeZone(
            price=tp1,
            label_fa="تارگت ۱ (Measured Move ۱۰۰٪)",
            label_en="TP1 (100% Measured Move)",
        ),
        tp2=TradeZone(
            price=tp2,
            label_fa="تارگت ۲ (اکستنشن ۱۶۱.۸٪)",
            label_en="TP2 (161.8% extension)",
        ),
    )


def _calc_expanded_flat_zones(
    *, p0: float, p1: float, p2: float, p3: float, p4: float,
    disp: float, atr: float, is_bull: bool, sign: float,
) -> PatternTradeZones:
    """
    Expanded Flat: B exceeds P1, C exceeds P2 (liquidity sweep).

    Entry A: Near P2 (risky, before the sweep).
    Entry B: At P4 after liquidity sweep and reversal candle.
    SL: At the extreme shadow of C (the sweep wick).
    TP: Larger targets due to energy stored in the sweep.
    """
    # SL at the C extreme (the wick of the sweep) with small buffer
    sl = p4 - sign * 0.3 * atr
    tp1 = p4 + sign * 1.272 * disp  # 127.2% (stronger due to sweep)
    tp2 = p4 + sign * 2.0 * disp  # 200% extension

    return PatternTradeZones(
        entry_a=TradeZone(
            price=p2,
            label_fa="ورود A (نزدیک P2 - قبل از سوییپ)",
            label_en="Entry A (near P2 - before sweep)",
        ),
        entry_b=TradeZone(
            price=p4,
            label_fa="ورود B (بعد از هانت نقدینگی)",
            label_en="Entry B (after liquidity sweep)",
        ),
        stop_loss=TradeZone(
            price=sl,
            label_fa="حد ضرر (سایه سوییپ C)",
            label_en="SL (C-wave sweep shadow)",
        ),
        tp1=TradeZone(
            price=tp1,
            label_fa="تارگت ۱ (اکستنشن ۱۲۷.۲٪)",
            label_en="TP1 (127.2% extension)",
        ),
        tp2=TradeZone(
            price=tp2,
            label_fa="تارگت ۲ (Measured Move ۲۰۰٪)",
            label_en="TP2 (200% extension)",
        ),
    )


def _calc_running_flat_zones(
    *, p0: float, p1: float, p2: float, p3: float, p4: float,
    disp: float, atr: float, is_bull: bool, sign: float,
) -> PatternTradeZones:
    """
    Running Flat: Shallow correction, B exceeds P1, C does NOT exceed A.

    Very strong continuation signal.
    Entry B is at P4 (shallow C), SL below P2 (the true support).
    """
    sl = p2 - sign * 0.5 * atr  # Below wave A end
    tp1 = p4 + sign * disp
    tp2 = p4 + sign * 1.618 * disp

    return PatternTradeZones(
        entry_a=TradeZone(
            price=p2,
            label_fa="ورود A (سطح P2 - تهاجمی)",
            label_en="Entry A (P2 level - aggressive)",
        ),
        entry_b=TradeZone(
            price=p4,
            label_fa="ورود B (اصلاح کم‌عمق P4)",
            label_en="Entry B (shallow P4 correction)",
        ),
        stop_loss=TradeZone(
            price=sl,
            label_fa="حد ضرر (زیر P2 - کف حمایت)",
            label_en="SL (below P2 - support floor)",
        ),
        tp1=TradeZone(
            price=tp1,
            label_fa="تارگت ۱ (Measured Move ۱۰۰٪)",
            label_en="TP1 (100% Measured Move)",
        ),
        tp2=TradeZone(
            price=tp2,
            label_fa="تارگت ۲ (اکستنشن ۱۶۱.۸٪)",
            label_en="TP2 (161.8% extension)",
        ),
    )


def _calc_default_zones(
    *, p0: float, p1: float, p2: float, p3: float, p4: float,
    disp: float, atr: float, is_bull: bool, sign: float,
) -> PatternTradeZones:
    """
    Default trade zones for contract_flat, complex_flat, or unknown patterns.

    Conservative approach: SL at P0 (widest safe level).
    """
    sl = p0 - sign * 0.5 * atr
    tp1 = p4 + sign * disp
    tp2 = p4 + sign * 1.618 * disp

    return PatternTradeZones(
        entry_a=TradeZone(
            price=p2,
            label_fa="ورود A (P2 - تهاجمی)",
            label_en="Entry A (P2 - aggressive)",
        ),
        entry_b=TradeZone(
            price=p4,
            label_fa="ورود B (P4 - محافظه‌کارانه)",
            label_en="Entry B (P4 - conservative)",
        ),
        stop_loss=TradeZone(
            price=sl,
            label_fa="حد ضرر (نزدیک P0 - امن)",
            label_en="SL (near P0 - safe)",
        ),
        tp1=TradeZone(
            price=tp1,
            label_fa="تارگت ۱ (Measured Move ۱۰۰٪)",
            label_en="TP1 (100% Measured Move)",
        ),
        tp2=TradeZone(
            price=tp2,
            label_fa="تارگت ۲ (اکستنشن ۱۶۱.۸٪)",
            label_en="TP2 (161.8% extension)",
        ),
    )


# Map category keys to their zone calculators
_ZONE_CALCULATORS = {
    "flag": _calc_flag_zones,
    "regular_flat": _calc_regular_flat_zones,
    "expanded_flat": _calc_expanded_flat_zones,
    "running_flat": _calc_running_flat_zones,
    "contract_flat": _calc_default_zones,
    "complex_flat": _calc_default_zones,
}
