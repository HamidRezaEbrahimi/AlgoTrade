# app/strategy/grid_manager.py
"""
Grid Manager.

Rules:
1. 25 Grid levels created between the 30-day major Support and Resistance range.
2. Grid is NEVER an entry signal on its own — used only for position sizing and capital distribution.
3. If 30-day range (Resistance - Support) / Support < 4%, Grid is automatically disabled.
"""
from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

import numpy as np

from app.models.grid import GridConfig


def calculate_30day_sr_range(
    highs: Sequence[float],
    lows: Sequence[float],
) -> tuple[float, float, float]:
    """
    Calculate 30-day major support, resistance, and percentage range.
    """
    if len(highs) == 0 or len(lows) == 0:
        return 0.0, 0.0, 0.0

    resistance = float(np.max(highs))
    support = float(np.min(lows))

    if support <= 0.0:
        return support, resistance, 0.0

    range_pct = (resistance - support) / support * 100.0
    return round(support, 6), round(resistance, 6), round(range_pct, 2)


def generate_symbol_grid(
    symbol: str,
    daily_highs: Sequence[float],
    daily_lows: Sequence[float],
    num_levels: int = 25,
    min_range_pct: float = 4.0,
) -> GridConfig:
    """
    Build a 25-level grid between 30-day S/R.
    Disables grid if range < 4%.
    """
    support, resistance, range_pct = calculate_30day_sr_range(daily_highs, daily_lows)

    grid = GridConfig(
        symbol=symbol,
        support=Decimal(str(support)),
        resistance=Decimal(str(resistance)),
        range_pct=Decimal(str(range_pct)),
        is_enabled=range_pct >= min_range_pct,
        total_levels=num_levels,
    )

    if grid.is_enabled:
        grid.calculate_levels()

    return grid


def get_grid_allocated_size(
    grid: GridConfig,
    entry_price: Decimal,
    total_trade_capital: Decimal,
) -> Decimal:
    """
    Calculate the portion of capital to allocate based on closest grid level.
    If grid is disabled, full trade capital is used.
    """
    if not grid.is_enabled or not grid.levels:
        return total_trade_capital

    # Find closest active grid level
    closest_level = min(grid.levels, key=lambda lvl: abs(lvl.price - entry_price))
    # Level allocation percentage of the trade
    level_weight = closest_level.allocation_pct / Decimal("100")
    allocated = total_trade_capital * level_weight * Decimal("25")  # normalized

    return min(allocated, total_trade_capital)
