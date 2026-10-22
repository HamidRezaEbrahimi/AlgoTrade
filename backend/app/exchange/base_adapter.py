# app/exchange/base_adapter.py
"""
Abstract Exchange Adapter Interface.

Defines the contract for all exchange integrations (Wallex, Nobitex, Paper Trading).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from app.models.candle import Candle
from app.models.order import Order, OrderSide, OrderType
from app.models.position import Position


class BaseExchangeAdapter(ABC):
    """Abstract base class for all exchange connectors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Exchange identifier (e.g. 'wallex', 'nobitex', 'paper')."""
        pass

    @abstractmethod
    async def get_balance(self) -> dict[str, Decimal]:
        """Fetch account balance (available & locked per asset)."""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> dict[str, Decimal]:
        """Fetch latest bid, ask, and last price for symbol."""
        pass

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        since: int | None = None,
    ) -> list[Candle]:
        """Fetch historical closed OHLCV candles."""
        pass

    @abstractmethod
    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal | None = None,
        client_order_id: str | None = None,
    ) -> Order:
        """Submit a new order with idempotent clientOrderId."""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str | None = None) -> bool:
        """Cancel an open order."""
        pass

    @abstractmethod
    async def cancel_all_orders(self, symbol: str | None = None) -> list[str]:
        """Emergency cancel all open orders."""
        pass

    @abstractmethod
    async def get_open_positions(self) -> list[Position]:
        """Fetch active positions directly from exchange."""
        pass

    @abstractmethod
    async def close_position(self, position: Position) -> bool:
        """Close an open position at current market price."""
        pass
