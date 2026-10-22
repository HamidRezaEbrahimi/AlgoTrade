# app/api/routes_backtest.py
"""
Backtest Execution & Reporting REST Endpoints.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.backtest.engine import BacktestEngine
from app.models.candle import Candle

router = APIRouter(prefix="/backtest", tags=["Backtesting"])


class BacktestRequest(BaseModel):
    symbol: str = "BTCUSDT"
    strategy_key: str = "price_action_8criteria"
    initial_capital: float = Field(10000.0, ge=100.0)
    fee_rate: float = Field(0.001, ge=0.0)
    slippage_rate: float = Field(0.0005, ge=0.0)


@router.post("/run")
async def run_backtest(req: BacktestRequest) -> dict[str, Any]:
    """
    Run an event-driven backtest simulation without look-ahead bias.
    """
    engine = BacktestEngine(
        initial_capital=req.initial_capital,
        fee_rate=req.fee_rate,
        slippage_rate=req.slippage_rate,
        strategy_key=req.strategy_key,
    )

    # Generate synthetic/sample closed candles sequence for testing
    now = datetime.now(UTC)
    candles_4h = []
    candles_1h = []
    candles_15m = []

    price = 60000.0
    for i in range(120):
        t4h = now - timedelta(hours=(120 - i) * 4)
        candles_4h.append(Candle(
            symbol=req.symbol, timeframe="4h", timestamp=t4h,
            open=Decimal(str(price)), high=Decimal(str(price + 200)),
            low=Decimal(str(price - 150)), close=Decimal(str(price + 50)),
            volume=Decimal("1500"),
        ))
        price += 30.0

    price = 60000.0
    for i in range(300):
        t1h = now - timedelta(hours=(300 - i))
        candles_1h.append(Candle(
            symbol=req.symbol, timeframe="1h", timestamp=t1h,
            open=Decimal(str(price)), high=Decimal(str(price + 100)),
            low=Decimal(str(price - 80)), close=Decimal(str(price + 20)),
            volume=Decimal("500"),
        ))
        price += 15.0

    price = 60000.0
    for i in range(600):
        t15 = now - timedelta(minutes=(600 - i) * 15)
        candles_15m.append(Candle(
            symbol=req.symbol, timeframe="15m", timestamp=t15,
            open=Decimal(str(price)), high=Decimal(str(price + 50)),
            low=Decimal(str(price - 40)), close=Decimal(str(price + 10)),
            volume=Decimal("150"),
        ))
        price += 5.0

    res = engine.run(req.symbol, candles_4h, candles_1h, candles_15m)

    return {
        "metrics": {
            "total_trades": res.metrics.total_trades,
            "win_rate_pct": res.metrics.win_rate_pct,
            "profit_factor": res.metrics.profit_factor,
            "max_drawdown_pct": res.metrics.max_drawdown_pct,
            "expectancy": res.metrics.expectancy,
            "total_pnl": res.metrics.total_pnl,
            "total_fees": res.metrics.total_fees,
            "avg_risk_reward": res.metrics.avg_risk_reward,
        },
        "equity_curve": [
            {
                "time": int(p.timestamp.timestamp()),
                "equity": p.equity,
                "drawdown_pct": p.drawdown_pct,
            }
            for p in res.equity_curve
        ],
        "trades": [
            {
                "id": str(t.id),
                "symbol": t.symbol,
                "direction": t.direction,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl": t.pnl,
                "risk_reward": t.risk_reward_actual,
                "exit_reason": t.exit_reason_code,
            }
            for t in res.trades
        ],
    }
