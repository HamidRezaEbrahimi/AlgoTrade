# app/market_data/scanner.py
"""
Multi-Symbol Market Scanner.

Rules:
- Scans liquid markets every 15 minutes, strictly after closed candles.
- Evaluates 8-criteria scores and ranks opportunities by score and R:R.
- Each symbol maintains independent status, orders, stop, and trailing.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from app.market_data.multi_tf import MultiTimeframeManager
from app.strategy.signal_scorer import evaluate_signal

logger = logging.getLogger("algotrade.market_data.scanner")


@dataclass
class ScannedOpportunity:
    """Represents a scanned symbol with evaluation metrics."""
    symbol: str
    direction: str
    total_score: int
    is_ready_to_enter: bool
    current_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    reason_fa: str
    scanned_at: datetime


class MarketScanner:
    """Scans and ranks trade opportunities across multiple liquid symbols."""

    def __init__(self, tf_manager: MultiTimeframeManager) -> None:
        self.tf_manager = tf_manager

    def scan_symbol(
        self,
        symbol: str,
        current_price: float,
    ) -> ScannedOpportunity | None:
        """Evaluate a single symbol across all 8 criteria."""
        payload = self.tf_manager.get_strategy_payload(symbol)
        if not payload:
            return None

        signal = evaluate_signal(symbol, payload, current_price)
        now = datetime.now(UTC)

        if signal:
            return ScannedOpportunity(
                symbol=symbol,
                direction=signal.direction,
                total_score=signal.scores.total,
                is_ready_to_enter=True,
                current_price=float(signal.entry_price),
                stop_loss=float(signal.stop_loss),
                take_profit=float(signal.take_profit_1),
                risk_reward=float(signal.risk_reward_ratio),
                reason_fa=signal.reason_description or "",
                scanned_at=now,
            )
        return None

    def scan_all_symbols(
        self,
        symbols_with_prices: list[tuple[str, float]],
    ) -> list[ScannedOpportunity]:
        """
        Scan all symbols and return ranked list of qualified opportunities.
        Ranked primarily by score (descending), then Risk/Reward (descending).
        """
        results: list[ScannedOpportunity] = []
        for symbol, price in symbols_with_prices:
            opp = self.scan_symbol(symbol, price)
            if opp:
                results.append(opp)

        # Sort: highest score first, then best R:R
        results.sort(key=lambda x: (x.total_score, x.risk_reward), reverse=True)
        logger.info(f"🔍 Scan completed: Found {len(results)} qualified opportunities.")
        return results
