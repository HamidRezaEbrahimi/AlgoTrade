# app/config/__init__.py
"""Configuration package — SSOT for all app settings."""

from app.config.settings import Settings, get_settings

__all__ = ["get_settings", "Settings"]
