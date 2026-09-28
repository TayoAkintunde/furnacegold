"""Persistent multi-level memory (Part 30).

Every write is redacted for secrets/emails and rejected if it still contains
personal data at a level that must not hold it. Customer knowledge is stored
only in aggregated/pseudonymous form.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aibos import paths, security
from aibos.schemas import stable_hash
from aibos.store import JsonlStore

LEVELS = ("global", "business", "project", "content", "customer", "experiment", "agent_learning")


class MemoryError_(ValueError):
    pass


class Memory:
    def __init__(self) -> None:
        self.root = paths.sub("memory")

    def _store(self, level: str) -> JsonlStore:
        if level not in LEVELS:
            raise MemoryError_(f"unknown memory level {level!r}; choose from {LEVELS}")
        return JsonlStore(self.root / f"{level}.jsonl")

    def write(self, level: str, kind: str, content: dict[str, Any], tags: list[str] | None = None,
              source: str = "") -> dict[str, Any]:
        text = security.redact(_flatten(content))
        if security.scan_secrets(text):
            raise MemoryError_("refusing to store content containing secrets")
        pii = security.scan_pii(text)
        if pii and level != "customer":
            raise MemoryError_(f"refusing to store personal data ({pii[0].pattern}) at level {level}")
        if pii and level == "customer":
            raise MemoryError_("customer memory stores aggregated/pseudonymous data only; remove personal data")
        record = {
            "id": stable_hash(level, kind, content),
            "level": level,
            "kind": kind,
            "content": _redact_obj(content),
            "tags": sorted(set(tags or [])),
            "source": source,
            "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        existing = {r["id"] for r in self._store(level)}
        if record["id"] not in existing:     # de-duplicate identical writes
            self._store(level).append(record)
        return record

    def read(self, level: str, kind: str | None = None, tag: str | None = None) -> list[dict[str, Any]]:
        out = self._store(level).all()
        if kind:
            out = [r for r in out if r["kind"] == kind]
        if tag:
            out = [r for r in out if tag in r.get("tags", [])]
        return out

    def search(self, query: str, levels: tuple[str, ...] = LEVELS) -> list[dict[str, Any]]:
        terms = [t for t in query.lower().split() if len(t) > 2]
        hits = []
        for lvl in levels:
            for r in self._store(lvl):
                blob = _flatten(r["content"]).lower() + " " + " ".join(r.get("tags", []))
                score = sum(blob.count(t) for t in terms)
                if score:
                    hits.append((score, r))
        return [r for _, r in sorted(hits, key=lambda x: -x[0])]

    def stats(self) -> dict[str, int]:
        return {lvl: len(self._store(lvl).all()) for lvl in LEVELS}


def _flatten(obj: Any) -> str:
    if isinstance(obj, dict):
        return " ".join(_flatten(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return " ".join(_flatten(v) for v in obj)
    return str(obj)


def _redact_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact_obj(v) for v in obj]
    if isinstance(obj, str):
        return security.redact(obj)
    return obj
