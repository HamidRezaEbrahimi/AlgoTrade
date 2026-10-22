# app/oms/idempotency.py
"""
Order Idempotency Manager.

Rule #3:
- Every outgoing order generates and attaches a unique clientOrderId (UUID4).
- Prevents double-ordering during network timeouts, retries, or reconnections.
"""
from __future__ import annotations

import uuid


class IdempotencyManager:
    """Tracks active and recent clientOrderIds to prevent double execution."""

    def __init__(self) -> None:
        self._processed_ids: set[str] = set()

    def generate_client_order_id(self, prefix: str = "algotrade") -> str:
        """Generate a cryptographically random UUID4 clientOrderId."""
        uid = str(uuid.uuid4())
        return f"{prefix}-{uid}"

    def is_duplicate(self, client_order_id: str) -> bool:
        """Check if an order ID has already been dispatched."""
        return client_order_id in self._processed_ids

    def register(self, client_order_id: str) -> None:
        """Register clientOrderId as dispatched."""
        self._processed_ids.add(client_order_id)
        # Keep set memory bounded
        if len(self._processed_ids) > 10000:
            # Pop oldest entries (clear half)
            self._processed_ids = set(list(self._processed_ids)[5000:])
