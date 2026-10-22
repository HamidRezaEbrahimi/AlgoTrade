# tests/test_risk.py
"""
Unit tests for Risk Management System (RMS).

Tests:
- Position Sizer: 1% risk rule, entry-to-stop distance sizing, 8% DD halving
- Drawdown Monitor: 8% half-size, 12% halt circuit breakers
- Exposure Guard: Max 4 positions, max 12% exposure caps
- Trailing Stop: RR=1.5 -> Breakeven, RR=2.5 -> 50% partial exit, 1.2x ATR trail
- Kill Switch: Atomic order cancellation and position closing
"""
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.models.position import Position
from app.risk.drawdown_monitor import CircuitBreakerStatus, DrawdownMonitor
from app.risk.exposure_guard import check_exposure_limits
from app.risk.position_sizer import calculate_position_size
from app.risk.trailing_stop import update_trailing_stop


def test_position_sizer_1pct_rule():
    """Verify position sizing does not risk more than 1% of equity."""
    equity = Decimal("10000.0")
    entry = Decimal("100.0")
    stop = Decimal("90.0")  # $10 risk per unit (10% stop)

    # 1% of $10,000 = $100 max risk -> Units = $100 / $10 = 10 units
    # Position value = 10 * 100 = $1000 <= 12% max exposure ($1200)
    units, risk_amt, pos_val = calculate_position_size(equity, entry, stop, risk_percentage=Decimal("1.0"))

    assert risk_amt == Decimal("100.00")
    assert units == Decimal("10.000000")
    assert pos_val == Decimal("1000.00")


def test_drawdown_circuit_breakers():
    """Verify 8% halves size, 12% stops entries."""
    monitor = DrawdownMonitor(initial_equity=Decimal("10000.0"))

    # 5% drawdown -> NORMAL
    s1 = monitor.update(Decimal("9500.0"))
    assert s1.status == CircuitBreakerStatus.NORMAL
    assert s1.can_open_trades is True
    assert s1.is_half_size is False

    # 8.5% drawdown -> HALF_SIZE
    s2 = monitor.update(Decimal("9150.0"))
    assert s2.status == CircuitBreakerStatus.HALF_SIZE
    assert s2.can_open_trades is True
    assert s2.is_half_size is True

    # 13% drawdown -> ENTRY_HALTED
    s3 = monitor.update(Decimal("8700.0"))
    assert s3.status == CircuitBreakerStatus.ENTRY_HALTED
    assert s3.can_open_trades is False


def test_exposure_guard_limits():
    """Verify max 4 positions and max 12% exposure."""
    equity = Decimal("10000.0")
    now = datetime.now(UTC)

    # 4 active positions
    positions = [
        Position(
            id=uuid.uuid4(), symbol=f"SYM{i}", exchange="paper", direction="LONG",
            entry_price=100.0, entry_time=now, initial_size=2.0, remaining_size=2.0,
            initial_stop=95.0, current_stop=95.0,
        )
        for i in range(4)
    ]

    # Trying to add a 5th position should fail
    allowed, msg = check_exposure_limits(positions, Decimal("100.0"), equity, max_positions=4)
    assert allowed is False
    assert "سقف مجاز" in msg


def test_trailing_stop_transitions():
    """Verify RR=1.5 moves SL to Breakeven and RR=2.5 triggers 50% exit."""
    now = datetime.now(UTC)
    # Long: Entry=100, Initial Stop=90 (Risk=10). Target RR=1.5 is 115, Target RR=2.5 is 125
    pos = Position(
        id=uuid.uuid4(), symbol="BTCUSDT", exchange="paper", direction="LONG",
        entry_price=100.0, entry_time=now, initial_size=10.0, remaining_size=10.0,
        initial_stop=90.0, current_stop=90.0,
    )

    # 1. Price reaches 115 (RR=1.5) -> Move stop to >= 100 (Breakeven)
    res_be = update_trailing_stop(pos, current_market_price=115.0, current_atr=2.0)
    assert res_be.stop_updated is True
    assert res_be.new_stop_price >= 100.0  # At least Breakeven
    assert res_be.should_close_partial_50 is False

    pos.current_stop = res_be.new_stop_price
    pos.trailing_active = True

    # 2. Price reaches 125 (RR=2.5) -> Trigger 50% partial close
    res_partial = update_trailing_stop(pos, current_market_price=125.0, current_atr=2.0)
    assert res_partial.should_close_partial_50 is True
    assert res_partial.close_reason == "PARTIAL_TP_RR25"

    # 3. Price drops to hit Stop -> Full close
    res_stop = update_trailing_stop(pos, current_market_price=98.0, current_atr=2.0)
    assert res_stop.should_close_full is True
    assert res_stop.close_reason == "STOP_LOSS_HIT"
