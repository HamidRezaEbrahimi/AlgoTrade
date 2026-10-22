# main.py
"""
AlgoTrade — FastAPI Application Entry Point.

Clean, concise (< 100 LOC), production-ready API and WebSocket server.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    ai_optimizer_router,
    ai_router,
    backtest_router,
    integrations_router,
    market_router,
    orders_router,
    patterns_router,
    settings_router,
    strategies_mgmt_router,
    strategy_router,
    system_router,
    ws_manager,
)
from app.api.routes_config import router as config_router
from app.config import get_settings
from app.db.database import init_db
from app.scheduler.cron_jobs import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
)
logger = logging.getLogger("algotrade.main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    logger.info(f"🚀 Starting AlgoTrade in [{settings.trading_mode.value}] mode...")
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"Database auto-init skipped (connect when ready): {e}")

    # Initialize strategy registry (load built-in YAML strategies)
    from app.strategy.strategy_registry import get_strategy_registry
    registry = get_strategy_registry()
    logger.info(f"📊 Loaded {registry.count} strategies")

    # Sync integration credentials from DB to adapters
    try:
        from app.exchange.faraz_adapter import sync_faraz_credentials_from_db
        await sync_faraz_credentials_from_db()
    except Exception as e:
        logger.warning(f"Could not sync Faraz credentials on startup: {e}")

    # Start Real-Time Market Streamer
    from app.market_data.market_streamer import get_market_streamer
    streamer = get_market_streamer()
    await streamer.start()

    start_scheduler()
    yield
    await streamer.stop()
    logger.info("🛑 AlgoTrade application shutting down...")


app = FastAPI(
    title="AlgoTrade API",
    description="Professional Multi-Market Algorithmic Trading Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount REST Routers ────────────────────────
app.include_router(system_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(strategy_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(patterns_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(integrations_router, prefix="/api")
app.include_router(ai_optimizer_router)
app.include_router(strategies_mgmt_router)


# ── WebSocket Real-Time Channel ───────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Real-time bi-directional streaming endpoint."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming subscriptions / ping
            if data == "ping":
                await websocket.send_text("pong")
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        ws_manager.disconnect(websocket)
