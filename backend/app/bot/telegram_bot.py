# app/bot/telegram_bot.py
"""
Telegram Bot Integration Client.

Broadcasts trading signals, trailing stop updates, and daily performance reports.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger("algotrade.bot.telegram")


class TelegramBotClient:
    """Telegram Bot API Connector."""

    BASE_URL = "https://api.telegram.org"

    def __init__(self, token: str, chat_ids: list[str] | None = None) -> None:
        self.token = token
        self.chat_ids = chat_ids or []
        self.client = httpx.AsyncClient(timeout=10.0)

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    async def send_message(self, text: str, chat_id: str | None = None, parse_mode: str = "Markdown") -> bool:
        """Send message to a specific chat or all configured chat IDs."""
        if not self.is_configured:
            return False

        targets = [chat_id] if chat_id else self.chat_ids
        if not targets:
            return False

        url = f"{self.BASE_URL}/bot{self.token}/sendMessage"
        success = True

        for cid in targets:
            try:
                resp = await self.client.post(
                    url,
                    json={
                        "chat_id": cid,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": True,
                    },
                )
                if resp.status_code != 200:
                    logger.warning(f"Telegram send error to {cid}: {resp.text}")
                    success = False
            except Exception as e:
                logger.error(f"Telegram post error to {cid}: {e}")
                success = False

        return success

    async def test_connection(self, chat_id: str | None = None) -> dict[str, Any]:
        """Test bot token validity and send verification ping."""
        if not self.token:
            return {"status": "error", "message": "Telegram Bot Token is empty."}

        url = f"{self.BASE_URL}/bot{self.token}/getMe"
        try:
            resp = await self.client.get(url)
            data = resp.json()
            if data.get("ok"):
                bot_username = data.get("result", {}).get("username", "")
                # Send test ping if chat_id provided
                if chat_id:
                    await self.send_message(
                        f"🤖 **تست اتصال موفق به سامانه AlgoTrade**\nربات @{bot_username} با موفقیت به سیستم متصل شد.",
                        chat_id=chat_id,
                    )
                return {
                    "status": "success",
                    "bot_name": data.get("result", {}).get("first_name", ""),
                    "username": f"@{bot_username}",
                    "message": f"Connected to @{bot_username}",
                }
            return {"status": "error", "message": f"Telegram API error: {data.get('description')}"}
        except Exception as e:
            return {"status": "error", "message": f"Connection error: {str(e)}"}
