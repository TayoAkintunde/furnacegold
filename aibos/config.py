"""YAML configuration loading (cached)."""
from __future__ import annotations

import functools
from typing import Any

import yaml

from aibos.paths import CONFIG_DIR


@functools.lru_cache(maxsize=None)
def load(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def settings() -> dict[str, Any]:
    return load("settings")


def platforms() -> dict[str, Any]:
    return load("platforms").get("platforms", {})


def stages() -> dict[str, Any]:
    return load("stages")


def pipelines() -> dict[str, Any]:
    return load("pipelines").get("pipelines", {})


def integrations() -> dict[str, Any]:
    return load("integrations").get("integrations", {})


def brand() -> dict[str, Any]:
    return load("brand").get("voice", {})


def taxonomy() -> dict[str, list[str]]:
    return load("taxonomy").get("taxonomy", {})


def revenue_streams() -> dict[str, Any]:
    return load("revenue_streams").get("revenue_streams", {})


def teaching() -> dict[str, Any]:
    return load("teaching")
