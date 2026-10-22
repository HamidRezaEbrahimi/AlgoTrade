# app/backtest/reporter.py
"""
Backtest Performance Metrics Reporter.

Calculates key quantitative metrics:
- Win Rate (%)
- Profit Factor
- Max Drawdown (%)
- Mathematical Expectancy ($/trade)
- Average Win / Average Loss
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.models.trade_log import TradeLog


@dataclass
class BacktestMetrics:
    """Comprehensive performance metrics summary."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    profit_factor: float
    max_drawdown_pct: float
    expectancy: float
    total_pnl: float
    total_fees: float
    avg_win: float
    avg_loss: float
    avg_risk_reward: float


def calculate_backtest_metrics(
    trades: list[TradeLog],
    initial_capital: float = 10000.0,
) -> BacktestMetrics:
    """Calculate summary statistics from a list of completed trade logs."""
    if not trades:
        return BacktestMetrics(
            total_trades=0, winning_trades=0, losing_trades=0,
            win_rate_pct=0.0, profit_factor=0.0, max_drawdown_pct=0.0,
            expectancy=0.0, total_pnl=0.0, total_fees=0.0,
            avg_win=0.0, avg_loss=0.0, avg_risk_reward=0.0,
        )

    pnls = [t.pnl for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]

    n_total = len(trades)
    n_wins = len(wins)
    n_losses = len(losses)

    win_rate = (n_wins / n_total * 100.0) if n_total > 0 else 0.0
    total_pnl = float(sum(pnls))
    total_fees = float(sum(t.total_fees for t in trades))

    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

    avg_win = float(np.mean(wins)) if wins else 0.0
    avg_loss = float(np.mean(losses)) if losses else 0.0

    # Expectancy = (Win% * AvgWin) - (Loss% * |AvgLoss|)
    win_prob = n_wins / n_total if n_total > 0 else 0.0
    loss_prob = n_losses / n_total if n_total > 0 else 0.0
    expectancy = (win_prob * avg_win) - (loss_prob * abs(avg_loss))

    # Calculate Max Drawdown from running equity
    running_equity = initial_capital
    peak = initial_capital
    max_dd_pct = 0.0

    for p in pnls:
        running_equity += p
        if running_equity > peak:
            peak = running_equity
        if peak > 0:
            dd = (peak - running_equity) / peak * 100.0
            if dd > max_dd_pct:
                max_dd_pct = dd

    avg_rr = float(np.mean([t.risk_reward_actual for t in trades])) if trades else 0.0

    return BacktestMetrics(
        total_trades=n_total,
        winning_trades=n_wins,
        losing_trades=n_losses,
        win_rate_pct=round(win_rate, 2),
        profit_factor=round(profit_factor, 2),
        max_drawdown_pct=round(max_dd_pct, 2),
        expectancy=round(expectancy, 2),
        total_pnl=round(total_pnl, 2),
        total_fees=round(total_fees, 2),
        avg_win=round(avg_win, 2),
        avg_loss=round(avg_loss, 2),
        avg_risk_reward=round(avg_rr, 2),
    )
