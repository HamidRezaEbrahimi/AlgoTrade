# app/bot/bale_bot.py
"""
Bale Messenger Bot Integration Client.

Connects to Iranian Bale Messenger API (https://tapi.bale.ai).
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger("algotrade.bot.bale")


class BaleBotClient:
    """Bale Messenger Bot API Connector."""

    BASE_URL = "https://tapi.bale.ai"

    def __init__(self, token: str, chat_ids: list[str] | None = None) -> None:
        self.token = token
        self.chat_ids = chat_ids or []
        self.client = httpx.AsyncClient(timeout=10.0)

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    async def send_message(self, text: str, chat_id: str | None = None) -> bool:
        """Send message to Bale chat."""
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
                    },
                )
                if resp.status_code != 200:
                    logger.warning(f"Bale send error to {cid}: {resp.text}")
                    success = False
            except Exception as e:
                logger.error(f"Bale post error to {cid}: {e}")
                success = False

        return success

    async def test_connection(self, chat_id: str | None = None) -> dict[str, Any]:
        """Test Bale bot token validity."""
        if not self.token:
            return {"status": "error", "message": "Bale Bot Token is empty."}

        url = f"{self.BASE_URL}/bot{self.token}/getMe"
        try:
            resp = await self.client.get(url)
            data = resp.json()
            if data.get("ok"):
                bot_username = data.get("result", {}).get("username", "")
                if chat_id:
                    await self.send_message(
                        "🤖 تست اتصال موفق به سامانه AlgoTrade\nربات بله با موفقیت به سیستم متصل شد.",
                        chat_id=chat_id,
                    )
                return {
                    "status": "success",
                    "bot_name": data.get("result", {}).get("first_name", ""),
                    "username": f"@{bot_username}",
                    "message": f"Connected to Bale @{bot_username}",
                }
            return {"status": "error", "message": f"Bale API error: {data.get('description')}"}
        except Exception as e:
            return {"status": "error", "message": f"Connection error: {str(e)}"}
