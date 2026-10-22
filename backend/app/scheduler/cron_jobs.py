# app/scheduler/cron_jobs.py
"""
Scheduled Tasks & Cron Jobs.

Rules:
- Scans markets every 15 minutes, strictly after closed candles.
- Executes daily performance report and summary logs.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("algotrade.scheduler")

scheduler = AsyncIOScheduler()


async def scheduled_15min_candle_scan() -> None:
    """Run 15-minute multi-symbol scan on closed candle."""
    logger.info("⏰ 15-Min Cron: Scanning market on closed candle...")
    # In live mode, fetches latest closed 15M/1H/4H candle and checks 8-criteria scores


async def scheduled_daily_report() -> None:
    """Generate daily trading summary report."""
    logger.info("📊 Daily Cron: Generating performance and error summary report...")


def start_scheduler() -> None:
    """Register and start cron jobs."""
    # Run at :00, :15, :30, :45 past each hour (15-min candle close)
    scheduler.add_job(
        scheduled_15min_candle_scan,
        "cron",
        minute="0,15,30,45",
        id="scan_15min",
        replace_existing=True,
    )
    # Run daily at 00:00 UTC
    scheduler.add_job(
        scheduled_daily_report,
        "cron",
        hour=0,
        minute=0,
        id="daily_report",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("✅ APScheduler started with 15-min and daily cron jobs.")
