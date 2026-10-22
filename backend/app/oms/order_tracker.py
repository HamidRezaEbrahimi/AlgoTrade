# app/oms/order_tracker.py
"""
Order Tracker & Execution Telemetry.

Tracks order latency, fill percentages, errors, retries, and API performance metrics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.models.order import Order, OrderStatus


@dataclass
class OrderTelemetry:
    """Telemetry data for a single order."""
    client_order_id: str
    symbol: str
    exchange: str
    dispatched_at: datetime
    filled_at: datetime | None = None
    latency_ms: float = 0.0
    retry_count: int = 0
    errors: list[str] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING


class OrderTracker:
    """Monitors live orders, latencies, and retry logs."""

    def __init__(self) -> None:
        self._telemetry: dict[str, OrderTelemetry] = {}
        self._daily_retry_count: int = 0
        self._daily_errors: list[dict[str, str]] = []

    def track_dispatch(self, order: Order) -> None:
        """Start tracking an outgoing order."""
        self._telemetry[order.client_order_id] = OrderTelemetry(
            client_order_id=order.client_order_id,
            symbol=order.symbol,
            exchange=order.exchange,
            dispatched_at=datetime.now(UTC),
            status=order.status,
        )

    def track_fill(self, client_order_id: str, filled_order: Order) -> None:
        """Record order completion and latency."""
        if client_order_id in self._telemetry:
            telem = self._telemetry[client_order_id]
            telem.filled_at = datetime.now(UTC)
            telem.latency_ms = (telem.filled_at - telem.dispatched_at).total_seconds() * 1000.0
            telem.status = filled_order.status

    def record_retry(self, client_order_id: str, error_msg: str) -> None:
        """Log an exchange API retry attempt."""
        self._daily_retry_count += 1
        self._daily_errors.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "order_id": client_order_id,
            "error": error_msg,
        })
        if client_order_id in self._telemetry:
            self._telemetry[client_order_id].retry_count += 1
            self._telemetry[client_order_id].errors.append(error_msg)

    def get_summary(self) -> dict[str, Any]:
        """Get daily execution telemetry summary."""
        total_tracked = len(self._telemetry)
        filled = [t for t in self._telemetry.values() if t.filled_at is not None]
        avg_latency = (
            sum(t.latency_ms for t in filled) / len(filled)
            if filled else 0.0
        )
        return {
            "total_orders": total_tracked,
            "filled_orders": len(filled),
            "avg_latency_ms": round(avg_latency, 2),
            "total_retries": self._daily_retry_count,
            "recent_errors": self._daily_errors[-20:],
        }
