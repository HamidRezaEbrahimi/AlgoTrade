# app/oms/order_executor.py
"""
Order Executor.

Mandatory pipeline: Signal -> RMS validation -> Exchange Adapter -> Database Position.
"""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.exchange.base_adapter import BaseExchangeAdapter
from app.models.order import OrderSide, OrderType
from app.models.position import Position, PositionStatus
from app.models.signal import Signal
from app.oms.idempotency import IdempotencyManager
from app.risk.exposure_guard import validate_pre_trade_pipeline

logger = logging.getLogger("algotrade.oms.executor")


class OrderExecutor:
    """Orchestrates order placement through pre-trade risk checks and exchange execution."""

    def __init__(
        self,
        adapter: BaseExchangeAdapter,
        idempotency_mgr: IdempotencyManager | None = None,
    ) -> None:
        self.adapter = adapter
        self.idempotency = idempotency_mgr or IdempotencyManager()

    async def execute_entry_signal(
        self,
        signal: Signal,
        position_size_units: Decimal,
        account_equity: Decimal,
        active_positions: list[Position],
        current_market_price: Decimal,
        can_open_trades: bool,
    ) -> tuple[Position | None, str]:
        """
        Safely execute an entry signal through the complete RMS pipeline.
        """
        position_value = position_size_units * current_market_price

        # 1. Pre-Trade Risk Checks (Mandatory RMS Pipeline)
        rms_result = validate_pre_trade_pipeline(
            signal_price=signal.entry_price,
            current_market_price=current_market_price,
            signal_timestamp=signal.timestamp,
            account_equity=account_equity,
            active_positions=active_positions,
            new_position_value=position_value,
            can_open_trades=can_open_trades,
        )

        if not rms_result.passed:
            logger.warning(f"❌ Order REJECTED by RMS: {rms_result.message_fa}")
            return None, rms_result.message_fa

        # 2. Idempotent clientOrderId generation
        cid = self.idempotency.generate_client_order_id()
        if self.idempotency.is_duplicate(cid):
            return None, "شناسه سفارش تکراری است."

        self.idempotency.register(cid)

        # 3. Exchange Order Dispatch
        side = OrderSide.BUY if signal.direction == "LONG" else OrderSide.SELL
        try:
            order = await self.adapter.create_order(
                symbol=signal.symbol,
                side=side,
                order_type=OrderType.MARKET,
                amount=position_size_units,
                price=signal.entry_price,
                client_order_id=cid,
            )
            logger.info(f"✅ Order dispatched: {order.client_order_id} ({order.status.value})")

            # 4. Create Initial Position
            position = Position(
                id=uuid.uuid4(),
                symbol=signal.symbol,
                exchange=self.adapter.name,
                direction=signal.direction,
                status=PositionStatus.OPEN,
                entry_price=float(signal.entry_price),
                entry_time=datetime.now(UTC),
                initial_size=float(position_size_units),
                remaining_size=float(position_size_units),
                initial_stop=float(signal.stop_loss),
                current_stop=float(signal.stop_loss),
                trailing_active=False,
                trailing_distance=None,
                tp1_price=float(signal.take_profit_1),
                tp2_price=float(signal.take_profit_2) if signal.take_profit_2 else None,
                tp1_hit=False,
                tp2_hit=False,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
            )
            return position, "سفارش با موفقیت ارسال و پوزیشن باز شد."

        except Exception as e:
            logger.error(f"❌ Exchange execution failed: {e}")
            return None, f"خطای ارسال سفارش به صرافی: {e}"
