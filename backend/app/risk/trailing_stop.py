# app/risk/trailing_stop.py
"""
Trailing Stop & Partial Exit Manager.

Rules:
1. When profit reaches RR = 1.5:
   - Move Stop Loss to Breakeven (entry price).
   - Activate Trailing Stop with trailing distance = 1.2 × ATR(14).
2. When profit reaches RR = 2.5:
   - Close 50% of position (Partial Take Profit).
   - Continue managing remaining 50% with Trailing Stop.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.position import Position


@dataclass
class TrailingUpdateResult:
    """Result of trailing stop evaluation for an open position."""
    position_id: str
    new_stop_price: float
    stop_updated: bool
    should_close_partial_50: bool
    is_breakeven_activated: bool
    should_close_full: bool
    close_reason: str | None
    description_fa: str


def update_trailing_stop(
    position: Position,
    current_market_price: float,
    current_atr: float,
    atr_multiplier: float = 1.2,
) -> TrailingUpdateResult:
    """
    Evaluate trailing stop logic and target hits on price updates.
    """
    entry = position.entry_price
    stop = position.current_stop
    is_long = position.direction.upper() == "LONG"
    initial_risk = abs(entry - position.initial_stop)

    if initial_risk <= 0.0:
        return TrailingUpdateResult(
            position_id=str(position.id),
            new_stop_price=stop,
            stop_updated=False,
            should_close_partial_50=False,
            is_breakeven_activated=False,
            should_close_full=False,
            close_reason=None,
            description_fa="ریسک اولیه صفر است.",
        )

    # Calculate current R:R multiple achieved
    current_gain = (current_market_price - entry) if is_long else (entry - current_market_price)
    current_rr = current_gain / initial_risk

    # 1. Check Stop Loss Hit
    is_stop_hit = (current_market_price <= stop) if is_long else (current_market_price >= stop)
    if is_stop_hit:
        return TrailingUpdateResult(
            position_id=str(position.id),
            new_stop_price=stop,
            stop_updated=False,
            should_close_partial_50=False,
            is_breakeven_activated=False,
            should_close_full=True,
            close_reason="STOP_LOSS_HIT",
            description_fa="حد ضرر یا حد ضرر دنباله‌دار لمس شد.",
        )

    new_stop = stop
    stop_updated = False
    be_activated = False
    partial_close = False
    trail_dist = current_atr * atr_multiplier

    # 2. Check RR >= 2.5: Close 50% and activate trailing for remainder
    if current_rr >= 2.5 and not position.tp2_hit:
        partial_close = True
        # Calculate dynamic trailing stop level
        proposed_stop = (current_market_price - trail_dist) if is_long else (current_market_price + trail_dist)
        if (is_long and proposed_stop > new_stop) or (not is_long and proposed_stop < new_stop):
            new_stop = round(proposed_stop, 6)
            stop_updated = True

        return TrailingUpdateResult(
            position_id=str(position.id),
            new_stop_price=new_stop,
            stop_updated=stop_updated,
            should_close_partial_50=True,
            is_breakeven_activated=False,
            should_close_full=False,
            close_reason="PARTIAL_TP_RR25",
            description_fa="تارگت RR=2.5 لمس شد: خروج ۵۰٪ پوزیشن و ادامه با حد ضرر دنباله‌دار.",
        )

    # 3. Check RR >= 1.5: Move SL to Breakeven and activate trailing
    if current_rr >= 1.5:
        # Proposed breakeven or trailing stop
        proposed_trail = (current_market_price - trail_dist) if is_long else (current_market_price + trail_dist)
        # Ensure stop is at least at Breakeven
        if is_long:
            target_stop = max(entry, proposed_trail)
            if target_stop > new_stop:
                new_stop = round(target_stop, 6)
                stop_updated = True
                be_activated = True
        else:
            target_stop = min(entry, proposed_trail)
            if target_stop < new_stop:
                new_stop = round(target_stop, 6)
                stop_updated = True
                be_activated = True

    # 4. If trailing was already active, trail forward
    elif position.trailing_active:
        proposed_trail = (current_market_price - trail_dist) if is_long else (current_market_price + trail_dist)
        if (is_long and proposed_trail > new_stop) or (not is_long and proposed_trail < new_stop):
            new_stop = round(proposed_trail, 6)
            stop_updated = True

    return TrailingUpdateResult(
        position_id=str(position.id),
        new_stop_price=new_stop,
        stop_updated=stop_updated,
        should_close_partial_50=partial_close,
        is_breakeven_activated=be_activated,
        should_close_full=False,
        close_reason=None,
        description_fa=(
            "حد ضرر به‌روزرسانی شد." if stop_updated else "موقعیت معاملاتی در وضعیت نرمال."
        ),
    )
