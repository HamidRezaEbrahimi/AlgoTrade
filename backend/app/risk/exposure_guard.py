# app/risk/exposure_guard.py
"""
Exposure Guard & Pre-Trade RMS Pipeline.

Rules:
- Maximum 4 simultaneous open positions.
- Maximum 12% total capital exposure across all open positions.
- Stale data check (reject signal if candle latency > 120s).
- Slippage check (reject if price moved > 0.5% from signal).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.models.position import Position, PositionStatus


@dataclass
class PreTradeCheckResult:
    """Outcome of pre-trade risk validations."""
    passed: bool
    reason_code: str
    message_fa: str


def check_exposure_limits(
    active_positions: list[Position],
    new_position_value: Decimal,
    account_equity: Decimal,
    max_positions: int = 4,
    max_exposure_pct: Decimal = Decimal("12.0"),
) -> tuple[bool, str]:
    """
    Ensure adding a new position does not breach position count or exposure caps.
    """
    open_count = sum(1 for p in active_positions if p.status in [PositionStatus.OPEN, PositionStatus.PARTIAL])
    if open_count >= max_positions:
        return False, f"تعداد پوزیشن‌های باز ({open_count}) به سقف مجاز ({max_positions}) رسیده است."

    current_exposure = sum(
        Decimal(str(p.remaining_size)) * Decimal(str(p.entry_price))
        for p in active_positions
        if p.status in [PositionStatus.OPEN, PositionStatus.PARTIAL]
    )

    total_projected_exposure = current_exposure + new_position_value
    max_allowed_exposure = (account_equity * max_exposure_pct) / Decimal("100")

    if total_projected_exposure > max_allowed_exposure:
        return False, (
            f"سرمایه درگیر پیش‌بینی شده ({total_projected_exposure:.2f}) "
            f"از سقف {max_exposure_pct}٪ سرمایه ({max_allowed_exposure:.2f}) فراتر می‌رود."
        )

    return True, "حدود سرمایه و تعداد پوزیشن مجاز است."


def validate_pre_trade_pipeline(
    signal_price: Decimal,
    current_market_price: Decimal,
    signal_timestamp: datetime,
    account_equity: Decimal,
    active_positions: list[Position],
    new_position_value: Decimal,
    can_open_trades: bool,
    max_slippage_pct: Decimal = Decimal("0.5"),
    max_candle_delay_sec: int = 120,
) -> PreTradeCheckResult:
    """
    Run complete mandatory Pre-Trade Risk Management System (RMS) pipeline.
    """
    # 1. Circuit breaker check
    if not can_open_trades:
        return PreTradeCheckResult(
            passed=False,
            reason_code="CIRCUIT_BREAKER_HALTED",
            message_fa="کلید قطع خودکار فعال است؛ ورود به معامله جدید متوقف شده.",
        )

    # 2. Stale data check
    now = datetime.now(UTC)
    candle_age = (now - signal_timestamp).total_seconds()
    if candle_age > max_candle_delay_sec:
        return PreTradeCheckResult(
            passed=False,
            reason_code="STALE_DATA",
            message_fa=f"داده منسوخ شده است (تأخیر: {candle_age:.0f} ثانیه، سقف: {max_candle_delay_sec} ثانیه).",
        )

    # 3. Slippage check
    price_divergence = abs(current_market_price - signal_price) / signal_price * Decimal("100")
    if price_divergence > max_slippage_pct:
        return PreTradeCheckResult(
            passed=False,
            reason_code="EXCESSIVE_SLIPPAGE",
            message_fa=f"لغزش قیمت بیش‌ازحد مجاز ({price_divergence:.2f}٪ > {max_slippage_pct}٪).",
        )

    # 4. Exposure & position count check
    exposure_ok, exposure_msg = check_exposure_limits(
        active_positions, new_position_value, account_equity
    )
    if not exposure_ok:
        return PreTradeCheckResult(
            passed=False,
            reason_code="EXPOSURE_LIMIT_EXCEEDED",
            message_fa=exposure_msg,
        )

    return PreTradeCheckResult(
        passed=True,
        reason_code="RMS_PASSED",
        message_fa="تمامی بررسی‌های مدیریت ریسک با موفقیت تأیید شدند.",
    )
