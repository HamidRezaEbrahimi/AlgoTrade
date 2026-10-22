# app/risk/kill_switch.py
"""
Emergency Kill-Switch.

Rule #1:
- Atomic, top-priority Kill-Switch mechanism.
- Immediately cancels all open orders across all exchanges.
- Closes all active positions (market or safe limit).
- Suspends all strategy engine executions.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("algotrade.risk.kill_switch")


@dataclass
class KillSwitchReport:
    """Report generated after Kill-Switch activation."""
    triggered_at: datetime
    user_id: str | None
    cancelled_orders_count: int
    closed_positions_count: int
    errors: list[str]
    success: bool
    message_fa: str


class KillSwitchManager:
    """Orchestrates emergency shutdown across exchange adapters and OMS."""

    _is_tripped: bool = False

    @classmethod
    def is_active(cls) -> bool:
        """Check if kill-switch is currently engaged."""
        return cls._is_tripped

    @classmethod
    def reset(cls) -> None:
        """Manually disengage kill-switch to resume operations."""
        cls._is_tripped = False
        logger.warning("🟢 Kill-Switch has been manually RESET. Trading engine can resume.")

    @classmethod
    async def trigger(
        cls,
        exchange_adapters: list[Any],
        open_positions: list[Any],
        user_id: str | None = None,
        close_positions: bool = True,
    ) -> KillSwitchReport:
        """
        Atomically trigger the emergency Kill-Switch.
        """
        cls._is_tripped = True
        triggered_time = datetime.now(UTC)
        logger.critical(f"🛑 EMERGENCY KILL-SWITCH ACTIVATED by user: {user_id}")

        cancelled_count = 0
        closed_count = 0
        errors: list[str] = []

        # 1. Cancel all open orders on all exchanges
        for adapter in exchange_adapters:
            try:
                cancelled = await adapter.cancel_all_orders()
                cancelled_count += len(cancelled)
                logger.info(f"Cancelled {len(cancelled)} orders on {adapter.name}")
            except Exception as e:
                err_msg = f"Failed to cancel orders on {getattr(adapter, 'name', 'exchange')}: {e}"
                logger.error(err_msg)
                errors.append(err_msg)

        # 2. Close all active positions if requested
        if close_positions:
            for pos in open_positions:
                try:
                    # Find matching exchange adapter
                    matched_adapter = next(
                        (a for a in exchange_adapters if a.name == pos.exchange), None
                    )
                    if matched_adapter:
                        await matched_adapter.close_position(pos)
                        closed_count += 1
                        logger.info(f"Emergency closed position {pos.id} ({pos.symbol})")
                except Exception as e:
                    err_msg = f"Failed to close position {pos.id}: {e}"
                    logger.error(err_msg)
                    errors.append(err_msg)

        success = len(errors) == 0
        msg_fa = (
            f"کلید قطع اضطراری فعال شد: {cancelled_count} سفارش لغو و {closed_count} پوزیشن بسته شد."
            if success
            else f"کلید قطع اضطراری با {len(errors)} خطا اجرا شد. لطفاً وضعیت صرافی را دستی بررسی کنید."
        )

        return KillSwitchReport(
            triggered_at=triggered_time,
            user_id=user_id,
            cancelled_orders_count=cancelled_count,
            closed_positions_count=closed_count,
            errors=errors,
            success=success,
            message_fa=msg_fa,
        )
