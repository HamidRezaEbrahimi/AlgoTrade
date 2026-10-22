# app/backtest/engine.py
"""
Backtesting Engine.

Rules:
- Strictly NO look-ahead bias: Signals and entries evaluated only on closed candles.
- Models execution fees, slippage, stop loss, trailing stop (1.2x ATR), and 50% partial exit at RR=2.5.
- Produces Equity Curve, trade history, Win Rate, Profit Factor, and Drawdown reports.
- Supports any strategy from StrategyRegistry (built-in or user YAML).
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.backtest.equity_curve import EquityPoint, build_equity_curve
from app.backtest.reporter import BacktestMetrics, calculate_backtest_metrics
from app.indicators.atr import get_latest_atr
from app.market_data.candle_buffer import CandleRingBuffer
from app.market_data.multi_tf import MultiTimeframeManager
from app.models.candle import Candle
from app.models.position import Position, PositionStatus
from app.models.trade_log import TradeLog
from app.risk.position_sizer import calculate_position_size
from app.risk.trailing_stop import update_trailing_stop
from app.strategy.base_strategy import BaseStrategy, StrategyEvalContext
from app.strategy.signal_scorer import evaluate_signal
from app.strategy.strategy_registry import get_strategy_registry

logger = logging.getLogger("algotrade.backtest.engine")


@dataclass
class BacktestResult:
    """Complete output of a backtest execution."""
    metrics: BacktestMetrics
    equity_curve: list[EquityPoint]
    trades: list[TradeLog]


class BacktestEngine:
    """Event-driven, bar-by-bar backtesting engine."""

    def __init__(
        self,
        initial_capital: float = 10000.0,
        fee_rate: float = 0.001,       # 0.1% fee
        slippage_rate: float = 0.0005,  # 0.05% slippage
        max_positions: int = 4,
        strategy_key: str = "price_action_8criteria",
        strategy: BaseStrategy | None = None,
    ) -> None:
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.max_positions = max_positions
        self.strategy_key = strategy_key
        self.strategy = strategy

        if self.strategy is None:
            registry = get_strategy_registry()
            self.strategy = registry.get(self.strategy_key)

    def run(
        self,
        symbol: str,
        candles_4h: list[Candle],
        candles_1h: list[Candle],
        candles_15m: list[Candle],
    ) -> BacktestResult:
        """
        Run backtest over chronological sequence of candles.
        """
        buffer = CandleRingBuffer(capacity=1000)
        tf_manager = MultiTimeframeManager(buffer)

        # Pre-seed 4H and 1H initial warmup bars
        warmup_4h = candles_4h[:20] if len(candles_4h) >= 20 else candles_4h
        warmup_1h = candles_1h[:30] if len(candles_1h) >= 30 else candles_1h
        buffer.add_candles(warmup_4h)
        buffer.add_candles(warmup_1h)

        equity = self.initial_capital
        active_position: Position | None = None
        completed_trades: list[TradeLog] = []

        # Iterate through 15M candles step-by-step
        for _i, c15 in enumerate(candles_15m[20:], start=20):
            buffer.add_candle(c15)
            curr_price = float(c15.close)
            curr_time = c15.timestamp

            # Also feed corresponding 1H/4H candles up to this timestamp
            matching_1h = [c for c in candles_1h if c.timestamp <= curr_time]
            matching_4h = [c for c in candles_4h if c.timestamp <= curr_time]
            if matching_1h:
                buffer.add_candle(matching_1h[-1])
            if matching_4h:
                buffer.add_candle(matching_4h[-1])

            # Get recent 1H ATR for trailing stop
            _, h1_h, h1_l, h1_c, _ = buffer.get_arrays(symbol, "1h", limit=20)
            atr_1h = get_latest_atr(h1_h, h1_l, h1_c, period=14) if len(h1_c) >= 14 else curr_price * 0.01

            # 1. Manage Active Position (Trailing Stop / Exits)
            if active_position is not None:
                trail_res = update_trailing_stop(active_position, curr_price, atr_1h)

                # Check Stop Loss Hit
                if trail_res.should_close_full:
                    exit_price = curr_price * (1 - self.slippage_rate if active_position.direction == "LONG" else 1 + self.slippage_rate)
                    pnl = (exit_price - active_position.entry_price) * active_position.remaining_size
                    total_pnl = active_position.realized_pnl + pnl
                    fee = (active_position.entry_price * active_position.initial_size + exit_price * active_position.remaining_size) * self.fee_rate
                    net_pnl = total_pnl - fee
                    equity += net_pnl

                    init_risk = abs(active_position.entry_price - active_position.initial_stop)
                    actual_rr = (exit_price - active_position.entry_price) / init_risk if init_risk > 0 else 0.0

                    trade_log = TradeLog(
                        id=uuid.uuid4(),
                        symbol=symbol,
                        exchange="backtest",
                        direction=active_position.direction,
                        entry_price=active_position.entry_price,
                        entry_time=active_position.entry_time,
                        entry_reason_code=f"STRATEGY_{self.strategy_key.upper()}",
                        exit_price=exit_price,
                        exit_time=curr_time,
                        exit_reason_code=trail_res.close_reason or "STOP_LOSS",
                        size=active_position.initial_size,
                        total_fees=round(fee, 2),
                        pnl=round(net_pnl, 2),
                        pnl_percent=round((net_pnl / (active_position.entry_price * active_position.initial_size)) * 100, 2),
                        risk_reward_actual=round(actual_rr, 2),
                        hold_duration=curr_time - active_position.entry_time,
                    )
                    completed_trades.append(trade_log)
                    active_position = None

                # Check 50% Partial Close at RR=2.5
                elif trail_res.should_close_partial_50 and not active_position.tp2_hit:
                    partial_units = active_position.initial_size * 0.5
                    exit_price = curr_price * (1 - self.slippage_rate if active_position.direction == "LONG" else 1 + self.slippage_rate)
                    partial_pnl = (exit_price - active_position.entry_price) * partial_units
                    active_position.realized_pnl += partial_pnl
                    active_position.remaining_size -= partial_units
                    active_position.tp2_hit = True

                elif trail_res.stop_updated:
                    active_position.current_stop = trail_res.new_stop_price
                    if trail_res.is_breakeven_activated:
                        active_position.tp1_hit = True
                        active_position.trailing_active = True

            # 2. Check New Entry Signal (only if no active position)
            elif active_position is None:
                signal = None

                if self.strategy is not None:
                    h4_o, h4_h, h4_l, h4_c, h4_v = buffer.get_arrays(symbol, "4h", limit=50)
                    h1_o, h1_h, h1_l, h1_c, h1_v = buffer.get_arrays(symbol, "1h", limit=50)
                    m15_o, m15_h, m15_l, m15_c, m15_v = buffer.get_arrays(symbol, "15m", limit=50)

                    ctx = StrategyEvalContext(
                        symbol=symbol,
                        current_price=curr_price,
                        timestamp=curr_time,
                        h4_opens=h4_o, h4_highs=h4_h, h4_lows=h4_l, h4_closes=h4_c, h4_volumes=h4_v,
                        h1_opens=h1_o, h1_highs=h1_h, h1_lows=h1_l, h1_closes=h1_c, h1_volumes=h1_v,
                        m15_opens=m15_o, m15_highs=m15_h, m15_lows=m15_l, m15_closes=m15_c, m15_volumes=m15_v,
                    )
                    signal = self.strategy.evaluate(ctx)
                else:
                    payload = tf_manager.get_strategy_payload(symbol)
                    if payload:
                        signal = evaluate_signal(symbol, payload, curr_price)

                if signal:
                    units, risk_amt, pos_val = calculate_position_size(
                        account_equity=Decimal(str(equity)),
                        entry_price=Decimal(str(curr_price)),
                        stop_loss_price=signal.stop_loss,
                        risk_percentage=Decimal("1.0"),
                    )
                    if units > Decimal("0"):
                        fill_price = curr_price * (1 + self.slippage_rate if signal.direction == "LONG" else 1 - self.slippage_rate)
                        active_position = Position(
                            id=uuid.uuid4(),
                            symbol=symbol,
                            exchange="backtest",
                            direction=signal.direction,
                            status=PositionStatus.OPEN,
                            entry_price=fill_price,
                            entry_time=curr_time,
                            initial_size=float(units),
                            remaining_size=float(units),
                            initial_stop=float(signal.stop_loss),
                            current_stop=float(signal.stop_loss),
                            trailing_active=False,
                            tp1_price=float(signal.take_profit_1),
                            tp2_price=float(signal.take_profit_2) if signal.take_profit_2 else None,
                        )

        metrics = calculate_backtest_metrics(completed_trades, self.initial_capital)
        equity_curve = build_equity_curve(completed_trades, self.initial_capital)

        return BacktestResult(
            metrics=metrics,
            equity_curve=equity_curve,
            trades=completed_trades,
        )
