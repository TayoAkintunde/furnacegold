"""Minimal append-only JSONL / JSON stores used by memory, performance, approvals, etc."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from aibos.schemas import to_jsonable


class JsonlStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: Any) -> None:
        with self.path.open("a") as fh:
            fh.write(json.dumps(to_jsonable(record), default=str, sort_keys=True) + "\n")

    def __iter__(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return iter(())
        with self.path.open() as fh:
            return iter([json.loads(line) for line in fh if line.strip()])

    def all(self) -> list[dict[str, Any]]:
        return list(iter(self))

    def rewrite(self, records: list[Any]) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w") as fh:
            for r in records:
                fh.write(json.dumps(to_jsonable(r), default=str, sort_keys=True) + "\n")
        tmp.replace(self.path)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(obj), indent=2, default=str, ensure_ascii=False))


def read_json(path: Path, default: Any = None) -> Any:
    return json.loads(path.read_text()) if path.exists() else default
