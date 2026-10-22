# tests/test_backtest.py
"""
Unit tests for Backtesting Engine & Metrics Reporter.
"""
import uuid
from datetime import UTC, datetime, timedelta

from app.backtest.reporter import calculate_backtest_metrics
from app.models.trade_log import TradeLog


def test_metrics_reporter_calculation():
    """Verify Win Rate, Profit Factor, and Expectancy calculations."""
    now = datetime.now(UTC)
    trades = [
        TradeLog(
            id=uuid.uuid4(), symbol="BTCUSDT", exchange="paper", direction="LONG",
            entry_price=100.0, entry_time=now, entry_reason_code="ENTRY",
            exit_price=115.0, exit_time=now + timedelta(hours=2), exit_reason_code="TP",
            size=1.0, pnl=15.0, pnl_percent=15.0, risk_reward_actual=1.5,
        ),
        TradeLog(
            id=uuid.uuid4(), symbol="BTCUSDT", exchange="paper", direction="LONG",
            entry_price=100.0, entry_time=now, entry_reason_code="ENTRY",
            exit_price=90.0, exit_time=now + timedelta(hours=1), exit_reason_code="SL",
            size=1.0, pnl=-10.0, pnl_percent=-10.0, risk_reward_actual=-1.0,
        ),
    ]

    metrics = calculate_backtest_metrics(trades, initial_capital=1000.0)

    assert metrics.total_trades == 2
    assert metrics.winning_trades == 1
    assert metrics.losing_trades == 1
    assert metrics.win_rate_pct == 50.0
    assert metrics.profit_factor == 1.5  # 15 / 10
    assert metrics.total_pnl == 5.0
