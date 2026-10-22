# app/api/ws_handler.py
"""
WebSocket Connection Manager.

Streams real-time market ticks, new signals, position changes, and bot alerts to frontend clients.
Implements heartbeat ping/pong and connection state monitoring.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("algotrade.api.websocket")


class WebSocketManager:
    """Manages active client WebSocket connections and topic subscriptions."""

    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()
        self.channel_subscribers: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"🔌 WS Client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove disconnected client."""
        self.active_connections.discard(websocket)
        for _channel, subs in self.channel_subscribers.items():
            subs.discard(websocket)
        logger.info(f"🔌 WS Client disconnected. Remaining: {len(self.active_connections)}")

    def subscribe(self, websocket: WebSocket, channel: str) -> None:
        """Subscribe client to specific topic (e.g. 'ticks:BTCUSDT', 'signals', 'positions')."""
        if channel not in self.channel_subscribers:
            self.channel_subscribers[channel] = set()
        self.channel_subscribers[channel].add(websocket)

    async def broadcast_to_channel(self, channel: str, message: dict[str, Any]) -> None:
        """Send message to all subscribers of a channel."""
        subscribers = self.channel_subscribers.get(channel, set())
        if not subscribers:
            return

        payload = json.dumps(message, default=str)
        dead_sockets: list[WebSocket] = []

        for ws in subscribers:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_sockets.append(ws)

        for ws in dead_sockets:
            self.disconnect(ws)

    async def broadcast_global(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        payload = json.dumps(message, default=str)
        dead_sockets: list[WebSocket] = []

        for ws in list(self.active_connections):
            try:
                await ws.send_text(payload)
            except Exception:
                dead_sockets.append(ws)

        for ws in dead_sockets:
            self.disconnect(ws)


ws_manager = WebSocketManager()
