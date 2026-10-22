# tests/test_oms.py
"""
Unit tests for Order Management System (Idempotency, Order Execution, Exit Manager).
"""
import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.exchange.paper_adapter import PaperExchangeAdapter
from app.models.position import PositionStatus
from app.models.signal import EntryScores, Signal
from app.oms.idempotency import IdempotencyManager
from app.oms.order_executor import OrderExecutor


def test_idempotency_manager():
    """Verify unique clientOrderId generation and duplicate prevention."""
    mgr = IdempotencyManager()
    cid1 = mgr.generate_client_order_id()
    cid2 = mgr.generate_client_order_id()

    assert cid1 != cid2
    assert mgr.is_duplicate(cid1) is False

    mgr.register(cid1)
    assert mgr.is_duplicate(cid1) is True


@pytest.mark.asyncio
async def test_order_executor_successful_entry():
    """Verify order executor flows through RMS and initializes position."""
    adapter = PaperExchangeAdapter()
    executor = OrderExecutor(adapter)

    scores = EntryScores(
        structure=True, location=True, pattern=True,
        momentum=True, rsi=True, volume=True,
        risk_reward=True, stop_valid=True,
    )
    sig = Signal(
        id=uuid.uuid4(),
        symbol="BTCUSDT",
        direction="LONG",
        timestamp=datetime.now(UTC),
        scores=scores,
        entry_price=Decimal("60000.0"),
        stop_loss=Decimal("58000.0"),
        take_profit_1=Decimal("63000.0"),
        take_profit_2=Decimal("65000.0"),
        risk_reward_ratio=Decimal("1.5"),
        reason_code="SIGNAL_CONFIRMED_LONG",
    )

    # 0.015 BTC * 60,000 = $900 position value <= 12% of $10,000 ($1200)
    pos, msg = await executor.execute_entry_signal(
        signal=sig,
        position_size_units=Decimal("0.015"),
        account_equity=Decimal("10000.0"),
        active_positions=[],
        current_market_price=Decimal("60000.0"),
        can_open_trades=True,
    )

    assert pos is not None
    assert pos.symbol == "BTCUSDT"
    assert pos.initial_size == 0.015
    assert pos.status == PositionStatus.OPEN
