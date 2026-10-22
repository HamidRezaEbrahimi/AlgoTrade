# app/strategy/strategy_registry.py
"""
Strategy Registry — Central manager for all strategies.

Discovers built-in YAML strategies from strategies/ directory
and user-created strategies from database.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.strategy.base_strategy import BaseStrategy, StrategyMetadata
from app.strategy.yaml_strategy import YAMLStrategy

logger = logging.getLogger("algotrade.strategy.registry")

# Built-in strategies directory
_BUILTIN_DIR = Path(__file__).parent / "strategies"


class StrategyRegistry:
    """Central registry for all trading strategies."""

    def __init__(self) -> None:
        self._strategies: dict[str, BaseStrategy] = {}
        self._metadata_cache: dict[str, StrategyMetadata] = {}

    def load_builtins(self) -> int:
        """Scan strategies/ directory and load all YAML files."""
        count = 0
        if not _BUILTIN_DIR.exists():
            logger.warning("Built-in strategies dir not found: %s", _BUILTIN_DIR)
            return 0

        for yaml_file in sorted(_BUILTIN_DIR.glob("*.yaml")):
            if yaml_file.name.startswith("_"):
                continue  # Skip schema and templates
            try:
                strategy = YAMLStrategy(yaml_path=str(yaml_file))
                meta = strategy.get_metadata()
                self._strategies[meta.key] = strategy
                self._metadata_cache[meta.key] = meta
                count += 1
                logger.info("Loaded built-in strategy: %s", meta.key)
            except Exception as e:
                logger.error("Failed to load %s: %s", yaml_file.name, e)

        return count

    def register(
        self,
        strategy: BaseStrategy,
        overwrite: bool = False,
    ) -> None:
        """Register a strategy instance."""
        meta = strategy.get_metadata()
        if meta.key in self._strategies and not overwrite:
            raise ValueError(f"Strategy '{meta.key}' already registered")
        self._strategies[meta.key] = strategy
        self._metadata_cache[meta.key] = meta

    def register_from_yaml(
        self,
        yaml_content: str,
        overwrite: bool = False,
    ) -> StrategyMetadata:
        """Register a strategy from raw YAML content string."""
        strategy = YAMLStrategy(yaml_content=yaml_content)
        errors = strategy.validate_config()
        if errors:
            raise ValueError(f"Invalid strategy YAML: {'; '.join(errors)}")
        meta = strategy.get_metadata()
        if meta.key in self._strategies and not overwrite:
            existing = self._metadata_cache.get(meta.key)
            if existing and existing.is_builtin:
                raise ValueError(
                    f"Cannot overwrite built-in strategy '{meta.key}'"
                )
        self._strategies[meta.key] = strategy
        self._metadata_cache[meta.key] = meta
        return meta

    def get(self, key: str) -> BaseStrategy | None:
        """Get a strategy by key."""
        return self._strategies.get(key)

    def get_metadata(self, key: str) -> StrategyMetadata | None:
        """Get strategy metadata by key."""
        return self._metadata_cache.get(key)

    def list_all(self) -> list[StrategyMetadata]:
        """List all registered strategy metadata."""
        return list(self._metadata_cache.values())

    def list_builtin(self) -> list[StrategyMetadata]:
        """List only built-in strategies."""
        return [m for m in self._metadata_cache.values() if m.is_builtin]

    def list_custom(self) -> list[StrategyMetadata]:
        """List only user-created strategies."""
        return [m for m in self._metadata_cache.values() if not m.is_builtin]

    def remove(self, key: str) -> bool:
        """Remove a strategy (only non-builtin)."""
        meta = self._metadata_cache.get(key)
        if meta and meta.is_builtin:
            raise ValueError(f"Cannot remove built-in strategy '{key}'")
        if key in self._strategies:
            del self._strategies[key]
            del self._metadata_cache[key]
            return True
        return False

    @property
    def count(self) -> int:
        return len(self._strategies)


# ── Singleton ────────────────────────────────────
_registry: StrategyRegistry | None = None


def get_strategy_registry() -> StrategyRegistry:
    """Get or create the global strategy registry singleton."""
    global _registry
    if _registry is None:
        _registry = StrategyRegistry()
        loaded = _registry.load_builtins()
        logger.info("Strategy registry initialized: %d built-in", loaded)
    return _registry
