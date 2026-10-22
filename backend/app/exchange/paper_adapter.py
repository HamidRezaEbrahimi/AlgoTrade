# app/exchange/paper_adapter.py
"""
Paper Trading Adapter (Simulation Environment).

Default trading mode — zero risk, full real-time order lifecycle simulation.
"""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.exchange.base_adapter import BaseExchangeAdapter
from app.models.candle import Candle
from app.models.order import Order, OrderSide, OrderStatus, OrderType
from app.models.position import Position, PositionStatus

logger = logging.getLogger("algotrade.exchange.paper")


class PaperExchangeAdapter(BaseExchangeAdapter):
    """Simulated exchange adapter for Paper Trading."""

    def __init__(
        self,
        initial_balance_usdt: Decimal = Decimal("10000.0"),
        fee_rate: Decimal = Decimal("0.001"),  # 0.1% maker/taker
        slippage_rate: Decimal = Decimal("0.0005"),  # 0.05%
    ) -> None:
        self.initial_balance = initial_balance_usdt
        self.balances: dict[str, Decimal] = {
            "USDT": initial_balance_usdt,
            "IRT": Decimal("500000000"),  # 500M Rial / Toman
        }
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.orders: dict[str, Order] = {}
        self.positions: dict[str, Position] = {}
        self.latest_prices: dict[str, Decimal] = {}

    @property
    def name(self) -> str:
        return "paper"

    def update_price(self, symbol: str, price: Decimal) -> None:
        """Update market price for order matching and position PnL."""
        self.latest_prices[symbol] = price

    async def get_balance(self) -> dict[str, Decimal]:
        return dict(self.balances)

    async def get_ticker(self, symbol: str) -> dict[str, Decimal]:
        price = self.latest_prices.get(symbol, Decimal("65000.0"))
        spread = price * Decimal("0.0002")
        return {
            "bid": price - spread,
            "ask": price + spread,
            "last": price,
        }

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        since: int | None = None,
    ) -> list[Candle]:
        return []

    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal | None = None,
        client_order_id: str | None = None,
    ) -> Order:
        cid = client_order_id or str(uuid.uuid4())
        exec_price = price or self.latest_prices.get(symbol, Decimal("65000.0"))

        # Apply slippage
        if side == OrderSide.BUY:
            fill_price = exec_price * (Decimal("1") + self.slippage_rate)
        else:
            fill_price = exec_price * (Decimal("1") - self.slippage_rate)

        cost = amount * fill_price
        fee = cost * self.fee_rate

        order = Order(
            id=uuid.uuid4(),
            client_order_id=cid,
            exchange_order_id=f"paper-{cid[:8]}",
            symbol=symbol,
            exchange=self.name,
            side=side,
            order_type=order_type,
            status=OrderStatus.FILLED,
            price=float(fill_price),
            amount=float(amount),
            filled=float(amount),
            cost=float(cost),
            fee=float(fee),
            created_at=datetime.now(UTC),
        )

        self.orders[cid] = order
        logger.info(f"[PAPER] Order FILLED: {side.value} {amount} {symbol} @ {fill_price:.2f}")
        return order

    async def cancel_order(self, order_id: str, symbol: str | None = None) -> bool:
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False

    async def cancel_all_orders(self, symbol: str | None = None) -> list[str]:
        cancelled = []
        for cid, o in self.orders.items():
            if o.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                o.status = OrderStatus.CANCELLED
                cancelled.append(cid)
        return cancelled

    async def get_open_positions(self) -> list[Position]:
        return [p for p in self.positions.values() if p.status != PositionStatus.CLOSED]

    async def close_position(self, position: Position) -> bool:
        pos_id = str(position.id)
        if pos_id in self.positions:
            self.positions[pos_id].status = PositionStatus.CLOSED
            logger.info(f"[PAPER] Closed position {pos_id} ({position.symbol})")
            return True
        return False
