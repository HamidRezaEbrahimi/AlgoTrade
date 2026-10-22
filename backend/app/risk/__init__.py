# app/risk/__init__.py
"""Risk Management System (RMS) package."""

from app.risk.drawdown_monitor import (
    CircuitBreakerStatus,
    DrawdownMonitor,
    DrawdownState,
)
from app.risk.exposure_guard import (
    PreTradeCheckResult,
    check_exposure_limits,
    validate_pre_trade_pipeline,
)
from app.risk.kill_switch import (
    KillSwitchManager,
    KillSwitchReport,
)
from app.risk.position_sizer import calculate_position_size
from app.risk.trailing_stop import (
    TrailingUpdateResult,
    update_trailing_stop,
)

__all__ = [
    "calculate_position_size",
    "DrawdownMonitor",
    "DrawdownState",
    "CircuitBreakerStatus",
    "check_exposure_limits",
    "validate_pre_trade_pipeline",
    "PreTradeCheckResult",
    "update_trailing_stop",
    "TrailingUpdateResult",
    "KillSwitchManager",
    "KillSwitchReport",
]
