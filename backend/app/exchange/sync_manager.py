# app/exchange/sync_manager.py
"""
Position & Order Synchronization Manager.

Rule #4:
- After any network drop or service restart, the system must first reconcile
  actual exchange orders and positions before resuming strategy execution.
"""
from __future__ import annotations

import logging

from app.exchange.base_adapter import BaseExchangeAdapter
from app.models.position import Position, PositionStatus

logger = logging.getLogger("algotrade.exchange.sync")


class ReconnectionSyncManager:
    """Synchronizes database state with real exchange state on reconnect."""

    @classmethod
    async def reconcile_positions(
        cls,
        adapter: BaseExchangeAdapter,
        db_positions: list[Position],
    ) -> tuple[list[Position], list[str]]:
        """
        Reconcile local open positions with exchange reality.
        Detects positions that were closed externally (e.g. liquidated, SL hit on exchange).
        """
        logger.info(f"🔄 Reconciling positions for exchange '{adapter.name}'...")
        changes: list[str] = []
        updated_positions: list[Position] = []

        try:
            exchange_positions = await adapter.get_open_positions()
            exchange_pos_map = {p.symbol: p for p in exchange_positions}

            for local_pos in db_positions:
                if local_pos.status not in [PositionStatus.OPEN, PositionStatus.PARTIAL]:
                    continue

                if local_pos.symbol not in exchange_pos_map:
                    # Position is closed on exchange but open in DB
                    local_pos.status = PositionStatus.CLOSED
                    msg = f"Position {local_pos.id} ({local_pos.symbol}) was closed on exchange while offline."
                    logger.warning(f"⚠️ {msg}")
                    changes.append(msg)
                else:
                    # Sync remaining size
                    remote = exchange_pos_map[local_pos.symbol]
                    if abs(local_pos.remaining_size - remote.remaining_size) > 0.0001:
                        local_pos.remaining_size = remote.remaining_size
                        msg = f"Position {local_pos.symbol} size updated to {remote.remaining_size}."
                        changes.append(msg)

                updated_positions.append(local_pos)

            logger.info(f"✅ Sync complete. Reconciled {len(updated_positions)} positions.")
            return updated_positions, changes

        except Exception as e:
            logger.error(f"❌ Failed to sync positions with exchange: {e}")
            return db_positions, [f"Sync failed: {e}"]
