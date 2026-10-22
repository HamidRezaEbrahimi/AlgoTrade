# app/config/i18n.py
"""
Internationalization (i18n) Helper — Backend translation loader.

Loads translations from YAML files in backend/i18n/{locale}/{namespace}.yaml.
Zero hardcoded strings in backend responses or notifications.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.config.settings import get_settings

I18N_DIR = Path(__file__).parent.parent.parent / "i18n"


@lru_cache
def _load_yaml_namespace(locale: str, namespace: str) -> dict[str, Any]:
    """Load a single YAML translation namespace with caching."""
    file_path = I18N_DIR / locale / f"{namespace}.yaml"
    if not file_path.exists():
        # Fallback to default locale or English
        fallback_path = I18N_DIR / "fa" / f"{namespace}.yaml"
        if not fallback_path.exists():
            fallback_path = I18N_DIR / "en" / f"{namespace}.yaml"
        if not fallback_path.exists():
            return {}
        file_path = fallback_path

    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def t(
    namespace: str,
    key: str,
    locale: str | None = None,
    default: str | None = None,
    **kwargs: Any,
) -> str:
    """
    Translate a key in a given namespace and locale.

    Example:
        t("bot", "trade_signal_alert", locale="fa")
        t("orders", "limit", locale="en")
    """
    settings = get_settings()
    loc = locale or settings.default_locale
    data = _load_yaml_namespace(loc, namespace)
    text = data.get(key, default or key)
    if kwargs and isinstance(text, str):
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return str(text)
