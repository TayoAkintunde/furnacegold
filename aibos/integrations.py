"""Integration status (Part 43). Status is computed, never assumed.

CONNECTED           adapter implemented here AND credentials/packages present
CREDENTIAL REQUIRED adapter implemented, but a credential env var is missing
NOT CONNECTED       no adapter implemented in this codebase
"""
from __future__ import annotations

import html
import importlib.util
import os
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from aibos import config

CONNECTED = "CONNECTED"
NOT_CONNECTED = "NOT CONNECTED"
CREDENTIAL_REQUIRED = "CREDENTIAL REQUIRED"
PACKAGE_REQUIRED = "PACKAGE REQUIRED"

IMPLEMENTED_ADAPTERS = {"anthropic", "http_fetch", "local_files", "metrics_csv"}


@dataclass
class IntegrationStatus:
    name: str
    status: str
    purpose: str
    detail: str


def status(name: str) -> IntegrationStatus:
    spec = config.integrations().get(name)
    if spec is None:
        return IntegrationStatus(name, NOT_CONNECTED, "", "not declared in config/integrations.yaml")
    purpose = spec.get("purpose", "")
    adapter = spec.get("adapter")
    if not adapter or adapter not in IMPLEMENTED_ADAPTERS:
        return IntegrationStatus(name, NOT_CONNECTED, purpose, "no adapter implemented yet")
    pkg = spec.get("python_package")
    if pkg and importlib.util.find_spec(pkg) is None:
        return IntegrationStatus(name, PACKAGE_REQUIRED, purpose, f"pip install {pkg}")
    env = spec.get("env", []) or []
    alt = spec.get("alt_env", []) or []
    if env and not all(os.environ.get(e) for e in env) and not (alt and any(os.environ.get(e) for e in alt)):
        missing = [e for e in env if not os.environ.get(e)]
        return IntegrationStatus(name, CREDENTIAL_REQUIRED, purpose, f"set {', '.join(missing)}")
    if spec.get("network"):
        return IntegrationStatus(name, CONNECTED, purpose,
                                 "adapter ready; network reachability is not pre-checked (a failed fetch is reported, never substituted)")
    return IntegrationStatus(name, CONNECTED, purpose, "ready")


def all_statuses() -> list[IntegrationStatus]:
    return [status(n) for n in config.integrations()]


def is_connected(name: str) -> bool:
    return status(name).status == CONNECTED


# --- http_fetch adapter -------------------------------------------------
_TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>|<[^>]+>", re.S | re.I)


def fetch_url(url: str, timeout: float = 20.0) -> dict[str, str]:
    """Fetch a URL and return its visible text. Raises on failure — the caller
    must report the failure, never substitute invented content."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("only http(s) URLs are supported")
    req = urllib.request.Request(url, headers={"User-Agent": "aibos-research/0.1 (+source capture)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (scheme checked)
        raw = resp.read(3_000_000).decode(resp.headers.get_content_charset() or "utf-8", "replace")
    title_m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    text = html.unescape(_TAG.sub(" ", raw))
    text = re.sub(r"\s+", " ", text).strip()
    return {
        "url": url,
        "title": html.unescape(title_m.group(1).strip()) if title_m else url,
        "text": text,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "retrieved_by": "aibos.http_fetch",
    }
