# app/oms/exit_manager.py
"""
Exit Manager.

Rules:
- Handles exits on:
  1. Stop Loss hit
  2. Bearish CHoCH (on 4H / 1H)
  3. Bearish rejection at Resistance / Order Block / FVG
  4. Partial 50% TP at RR=2.5
  5. Trailing Stop trigger
- Generates finalized TradeLog records for performance reporting.
"""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.exchange.base_adapter import BaseExchangeAdapter
from app.models.order import OrderSide, OrderType
from app.models.position import Position, PositionStatus
from app.models.trade_log import TradeLog
from app.risk.trailing_stop import update_trailing_stop

logger = logging.getLogger("algotrade.oms.exit")


class ExitManager:
    """Manages active position exits and records trade logs."""

    def __init__(self, adapter: BaseExchangeAdapter) -> None:
        self.adapter = adapter

    async def check_and_execute_exit(
        self,
        position: Position,
        current_price: float,
        current_atr: float,
        has_bearish_choch: bool = False,
        has_resistance_rejection: bool = False,
    ) -> tuple[Position, TradeLog | None]:
        """
        Evaluate all exit conditions for an open position and execute if triggered.
        """
        if position.status == PositionStatus.CLOSED:
            return position, None

        now = datetime.now(UTC)

        # 1. Structural Exit: Bearish CHoCH or Resistance Rejection
        if position.direction.upper() == "LONG" and (has_bearish_choch or has_resistance_rejection):
            reason_code = "CHOCH_BEARISH" if has_bearish_choch else "RESISTANCE_REJECTION"
            reason_desc = (
                "خروج اضطراری: تغییر کاراکتر نزولی (CHoCH)"
                if has_bearish_choch
                else "خروج در مقاومت: تأیید بازگشت قیمت روی مقاومت/OB/FVG"
            )
            return await self._close_full(position, current_price, reason_code, reason_desc, now)

        # 2. Trailing Stop & Partial Exit Evaluation
        trail_res = update_trailing_stop(position, current_price, current_atr)

        # Handle Stop Loss / Trailing Hit
        if trail_res.should_close_full:
            return await self._close_full(
                position, current_price, trail_res.close_reason or "STOP_LOSS", trail_res.description_fa, now
            )

        # Handle Partial Close (50% at RR=2.5)
        if trail_res.should_close_partial_50 and not position.tp2_hit:
            close_units = Decimal(str(position.initial_size * 0.5))
            side = OrderSide.SELL if position.direction == "LONG" else OrderSide.BUY
            try:
                await self.adapter.create_order(
                    symbol=position.symbol,
                    side=side,
                    order_type=OrderType.MARKET,
                    amount=close_units,
                )
                position.status = PositionStatus.PARTIAL
                position.tp2_hit = True
                position.remaining_size -= float(close_units)
                partial_pnl = (current_price - position.entry_price) * float(close_units)
                position.realized_pnl += partial_pnl
                logger.info(f"💰 Partial TP executed for {position.symbol}: closed 50% @ {current_price:.2f}")
            except Exception as e:
                logger.error(f"Failed to execute partial close for {position.symbol}: {e}")

        # Update position stop price if modified
        if trail_res.stop_updated:
            position.current_stop = trail_res.new_stop_price
            if trail_res.is_breakeven_activated:
                position.tp1_hit = True
                position.trailing_active = True

        return position, None

    async def _close_full(
        self,
        position: Position,
        exit_price: float,
        reason_code: str,
        reason_desc: str,
        exit_time: datetime,
    ) -> tuple[Position, TradeLog]:
        """Execute market close order for remaining size and return TradeLog."""
        close_units = Decimal(str(position.remaining_size))
        side = OrderSide.SELL if position.direction == "LONG" else OrderSide.BUY

        try:
            await self.adapter.create_order(
                symbol=position.symbol,
                side=side,
                order_type=OrderType.MARKET,
                amount=close_units,
            )
        except Exception as e:
            logger.error(f"Error dispatching close order for {position.symbol}: {e}")

        position.status = PositionStatus.CLOSED
        final_pnl = (exit_price - position.entry_price) * position.remaining_size
        total_pnl = position.realized_pnl + final_pnl
        pnl_pct = (total_pnl / (position.entry_price * position.initial_size)) * 100.0 if position.entry_price > 0 else 0.0

        initial_risk = abs(position.entry_price - position.initial_stop)
        actual_rr = (exit_price - position.entry_price) / initial_risk if initial_risk > 0 else 0.0

        trade_log = TradeLog(
            id=uuid.uuid4(),
            symbol=position.symbol,
            exchange=position.exchange,
            direction=position.direction,
            entry_price=position.entry_price,
            entry_time=position.entry_time,
            entry_reason_code="PRICE_ACTION_8CRITERIA",
            entry_reason_text="سیگنال براساس ۸ معیار پرایس اکشن",
            exit_price=exit_price,
            exit_time=exit_time,
            exit_reason_code=reason_code,
            exit_reason_text=reason_desc,
            size=position.initial_size,
            total_fees=0.0,
            pnl=round(total_pnl, 2),
            pnl_percent=round(pnl_pct, 2),
            risk_reward_actual=round(actual_rr, 2),
            hold_duration=exit_time - position.entry_time,
        )

        logger.info(f"🏁 Closed Position {position.symbol}: PnL={total_pnl:.2f} ({reason_code})")
        return position, trade_log
