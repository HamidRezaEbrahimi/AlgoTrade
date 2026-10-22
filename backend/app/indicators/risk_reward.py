# app/indicators/risk_reward.py
"""
Risk / Reward Ratio Calculator.

Calculates theoretical and actual R:R ratios and validates targets.
Criteria #7: Risk/Reward ≥ 1.5.
"""
from __future__ import annotations


def calculate_risk_reward(
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    direction: str = "LONG",
) -> float:
    """
    Calculate the Risk/Reward ratio.

    For LONG: (take_profit - entry_price) / (entry_price - stop_loss)
    For SHORT: (entry_price - take_profit) / (stop_loss - entry_price)

    Returns:
        float: R:R ratio (e.g. 1.5, 2.0). Returns 0.0 if invalid.
    """
    if direction.upper() == "LONG":
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
    else:  # SHORT
        risk = stop_loss - entry_price
        reward = entry_price - take_profit

    if risk <= 0.0 or reward <= 0.0:
        return 0.0

    return round(reward / risk, 4)


def validate_risk_reward(
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    direction: str = "LONG",
    min_rr: float = 1.5,
) -> tuple[bool, float]:
    """
    Validate if the proposed trade meets the minimum R:R threshold (default 1.5).

    Returns:
        (is_valid, calculated_rr)
    """
    rr = calculate_risk_reward(entry_price, stop_loss, take_profit, direction)
    return rr >= min_rr, rr


def calculate_target_by_rr(
    entry_price: float,
    stop_loss: float,
    target_rr: float = 1.5,
    direction: str = "LONG",
) -> float:
    """
    Calculate target price given entry, stop loss, and desired R:R ratio.
    """
    if direction.upper() == "LONG":
        risk = entry_price - stop_loss
        return round(entry_price + (risk * target_rr), 6)
    else:
        risk = stop_loss - entry_price
        return round(entry_price - (risk * target_rr), 6)
