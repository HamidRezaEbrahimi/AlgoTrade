# app/risk/drawdown_monitor.py
"""
Drawdown Monitor & Circuit Breaker.

Rules:
- At 8% Drawdown from peak equity: Halve new trade position size (0.5% risk).
- At 12% Drawdown from peak equity: Trip circuit breaker — Halt all new trade entries.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class CircuitBreakerStatus(StrEnum):
    NORMAL = "NORMAL"                # Normal 1% risk per trade
    HALF_SIZE = "HALF_SIZE"          # 8% DD -> 0.5% risk per trade
    ENTRY_HALTED = "ENTRY_HALTED"    # 12% DD -> 0% risk (no new trades)


@dataclass
class DrawdownState:
    """Current state of account drawdown."""
    peak_equity: Decimal
    current_equity: Decimal
    drawdown_pct: Decimal
    status: CircuitBreakerStatus
    can_open_trades: bool
    is_half_size: bool
    message_fa: str


class DrawdownMonitor:
    """Monitors peak-to-trough equity drawdown and controls circuit breakers."""

    def __init__(
        self,
        initial_equity: Decimal,
        half_size_pct: Decimal = Decimal("8.0"),
        stop_entry_pct: Decimal = Decimal("12.0"),
    ) -> None:
        self.peak_equity = initial_equity
        self.half_size_pct = half_size_pct
        self.stop_entry_pct = stop_entry_pct

    def update(self, current_equity: Decimal) -> DrawdownState:
        """Update equity and recalculate drawdown status."""
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        if self.peak_equity <= Decimal("0"):
            dd_pct = Decimal("0")
        else:
            dd_pct = ((self.peak_equity - current_equity) / self.peak_equity) * Decimal("100")

        dd_pct = max(Decimal("0"), dd_pct)

        if dd_pct >= self.stop_entry_pct:
            status = CircuitBreakerStatus.ENTRY_HALTED
            can_open = False
            half_size = True
            msg = f"🛑 ورود جدید متوقف شد! افت سرمایه ({dd_pct:.2f}٪) از حد مجاز ۱۲٪ فراتر رفته است."
        elif dd_pct >= self.half_size_pct:
            status = CircuitBreakerStatus.HALF_SIZE
            can_open = True
            half_size = True
            msg = f"⚠️ حجم معاملات نصف شد! افت سرمایه ({dd_pct:.2f}٪) از ۸٪ فراتر رفته است."
        else:
            status = CircuitBreakerStatus.NORMAL
            can_open = True
            half_size = False
            msg = f"وضعیت سرمایه عادی است (افت فعلی: {dd_pct:.2f}٪)."

        return DrawdownState(
            peak_equity=self.peak_equity,
            current_equity=current_equity,
            drawdown_pct=round(dd_pct, 2),
            status=status,
            can_open_trades=can_open,
            is_half_size=half_size,
            message_fa=msg,
        )
