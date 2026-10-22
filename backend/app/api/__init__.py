# app/api/__init__.py
"""API Package barrel export."""

from app.api.routes_ai_agent import router as ai_router
from app.api.routes_ai_optimizer import router as ai_optimizer_router
from app.api.routes_backtest import router as backtest_router
from app.api.routes_integrations import router as integrations_router
from app.api.routes_market import router as market_router
from app.api.routes_orders import router as orders_router
from app.api.routes_patterns import router as patterns_router
from app.api.routes_settings import router as settings_router
from app.api.routes_strategies import router as strategies_mgmt_router
from app.api.routes_strategy import router as strategy_router
from app.api.routes_system import router as system_router
from app.api.ws_handler import ws_manager

__all__ = [
    "market_router",
    "strategy_router",
    "orders_router",
    "patterns_router",
    "backtest_router",
    "system_router",
    "strategies_mgmt_router",
    "settings_router",
    "ai_router",
    "integrations_router",
    "ai_optimizer_router",
    "ws_manager",
]
