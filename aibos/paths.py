"""Filesystem layout. Runtime state lives under AIBOS_DATA_DIR (default ./data)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_DIR = ROOT / "agents" / "registry"
PROMPTS_DIR = ROOT / "agents" / "prompts"
CONFIG_DIR = ROOT / "config"


def data_dir() -> Path:
    d = Path(os.environ.get("AIBOS_DATA_DIR", ROOT / "data"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def sub(name: str) -> Path:
    p = data_dir() / name
    p.mkdir(parents=True, exist_ok=True)
    return p
