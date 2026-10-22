#!/usr/bin/env python3
# backend/scripts/verify_all_timeframes.py
"""
Automated Multi-Timeframe Scanner & Diagnostics CLI for AlgoTrade.
Executes pattern analysis across 1m, 5m, 15m, 30m, 1h, 4h, 1d timeframes
and prints a diagnostic table of detected patterns, score, and latency.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.exchange.faraz_adapter import FarazDataAdapter, sync_faraz_credentials_from_db
from app.market_data.market_analyzer import MarketAnalyzer
from tests.test_multi_timeframe_alef import _generate_synthetic_wave_candles

TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]


async def run_diagnostics(symbol: str = "FXCM_XAUUSD", exchange: str = "faraz", limit: int = 1500) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 95)
    print(f"  ALGOTRADE AUTOMATED MULTI-TIMEFRAME DIAGNOSTICS: {symbol} [{exchange.upper()}]")
    print("=" * 95)

    fa: FarazDataAdapter | None = None
    if exchange.lower() == "faraz":
        await sync_faraz_credentials_from_db()
        fa = FarazDataAdapter()

    results: list[dict[str, Any]] = []

    for tf in TIMEFRAMES:
        candles = []
        is_live = False
        fetch_err = None

        if fa:
            try:
                candles = await fa.get_candles(symbol, tf, limit=limit)
                if candles:
                    is_live = True
            except Exception as e:
                fetch_err = str(e)

        if not candles:
            candles = _generate_synthetic_wave_candles(count=min(limit, 500), timeframe=tf)

        t_start = time.perf_counter()
        analysis = MarketAnalyzer.analyze_candles(candles, symbol=symbol, timeframe=tf)
        latency_ms = (time.perf_counter() - t_start) * 1000.0

        pats = analysis.get("detected_patterns", [])
        score = analysis.get("score", 0)
        signal = analysis.get("trade_setup", {}).get("signal", "WAIT")
        stage = analysis.get("stage", "")

        results.append({
            "tf": tf,
            "candles_count": len(candles),
            "is_live": is_live,
            "patterns_count": len(pats),
            "score": score,
            "signal": signal,
            "stage": stage,
            "latency_ms": latency_ms,
            "status": "PASS" if analysis.get("status") == "ok" else "FAIL",
            "fetch_err": fetch_err,
        })

    # Print Table
    header = f"{'Timeframe':<10} | {'Type':<8} | {'Candles':<8} | {'Patterns':<10} | {'Stage':<18} | {'Score':<6} | {'Signal':<7} | {'Latency':<9} | {'Status'}"
    print(header)
    print("-" * 95)

    for r in results:
        typ = "Live" if r["is_live"] else "Synthetic"
        st = r["stage"] or "-"
        sig = r["signal"] or "WAIT"
        line = (
            f"{r['tf']:<10} | {typ:<8} | {r['candles_count']:<8} | "
            f"{r['patterns_count']:<10} | {st[:18]:<18} | {r['score']}/8    | "
            f"{sig:<7} | {r['latency_ms']:<6.1f} ms | {r['status']}"
        )
        print(line)

    print("-" * 95)
    all_passed = all(r["status"] == "PASS" for r in results)
    print(f"Overall Result: {'ALL 7 TIMEFRAMES PASSED [OK]' if all_passed else 'SOME TIMEFRAMES FAILED'}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Timeframe Diagnostics CLI")
    parser.add_argument("--symbol", default="FXCM_XAUUSD", help="Symbol to test")
    parser.add_argument("--exchange", default="faraz", help="Exchange (faraz, ccxt)")
    parser.add_argument("--limit", type=int, default=1500, help="Candles count")
    args = parser.parse_args()

    asyncio.run(run_diagnostics(symbol=args.symbol, exchange=args.exchange, limit=args.limit))
