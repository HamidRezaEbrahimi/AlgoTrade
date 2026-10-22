# app/backtest/equity_curve.py
"""
Equity Curve Data Structure.

Generates timestamped equity series for frontend chart visualization.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.models.trade_log import TradeLog


@dataclass
class EquityPoint:
    """A single point on the equity curve."""
    timestamp: datetime
    equity: float
    drawdown_pct: float


def build_equity_curve(
    trades: list[TradeLog],
    initial_capital: float = 10000.0,
) -> list[EquityPoint]:
    """
    Construct continuous equity points from chronological trade history.
    """
    if not trades:
        return []

    sorted_trades = sorted(trades, key=lambda t: t.exit_time)
    points: list[EquityPoint] = [
        EquityPoint(
            timestamp=sorted_trades[0].entry_time,
            equity=initial_capital,
            drawdown_pct=0.0,
        )
    ]

    current_equity = initial_capital
    peak = initial_capital

    for trade in sorted_trades:
        current_equity += trade.pnl
        if current_equity > peak:
            peak = current_equity

        dd_pct = ((peak - current_equity) / peak * 100.0) if peak > 0 else 0.0
        points.append(
            EquityPoint(
                timestamp=trade.exit_time,
                equity=round(current_equity, 2),
                drawdown_pct=round(max(0.0, dd_pct), 2),
            )
        )

    return points
