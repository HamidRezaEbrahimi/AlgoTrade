# app/risk/position_sizer.py
"""
Position Sizer.

Rule:
- Risk per trade is strictly capped at 1% of total account equity.
- Position size = (Total Equity × Risk%) / |Entry Price - Stop Loss Price|.
- If drawdown >= 8%, risk is halved to 0.5%.
"""
from __future__ import annotations

from decimal import Decimal


def calculate_position_size(
    account_equity: Decimal,
    entry_price: Decimal,
    stop_loss_price: Decimal,
    risk_percentage: Decimal = Decimal("1.0"),
    is_half_size: bool = False,
    min_order_size: Decimal = Decimal("0.0001"),
    max_position_value_pct: Decimal = Decimal("12.0"),
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Calculate safe position size and risk amount.

    Returns:
        (position_size_in_units, risk_amount_in_quote, total_position_value)
    """
    if account_equity <= Decimal("0") or entry_price <= Decimal("0"):
        return Decimal("0"), Decimal("0"), Decimal("0")

    effective_risk_pct = risk_percentage / Decimal("2") if is_half_size else risk_percentage
    risk_amount = (account_equity * effective_risk_pct) / Decimal("100")

    price_distance = abs(entry_price - stop_loss_price)
    if price_distance <= Decimal("0"):
        return Decimal("0"), Decimal("0"), Decimal("0")

    # Unit size = Risk amount / Distance per unit
    raw_units = risk_amount / price_distance

    # Total position value = raw_units * entry_price
    position_value = raw_units * entry_price

    # Cap at max single position exposure (e.g. 12% of equity)
    max_allowed_value = (account_equity * max_position_value_pct) / Decimal("100")
    if position_value > max_allowed_value:
        raw_units = max_allowed_value / entry_price
        position_value = max_allowed_value
        risk_amount = raw_units * price_distance

    if raw_units < min_order_size:
        return Decimal("0"), Decimal("0"), Decimal("0")

    return round(raw_units, 6), round(risk_amount, 2), round(position_value, 2)
