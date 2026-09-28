"""Screen-recording content database and workflow (Parts 8 and 11 of the teaching brief).

One record per teaching opportunity. Workflow:
  RESEARCHED -> SELECTED -> READY_TO_RECORD -> RECORDED -> EDITING -> READY_TO_PUBLISH -> PUBLISHED -> ANALYZED
(plus REJECTED from any non-terminal state).

The system only sets RESEARCHED, READY_TO_RECORD and ANALYZED. The owner makes every other move,
including PUBLISHED, which records that *they* published it. The system never publishes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aibos import config, paths
from aibos.rules import content_words
from aibos.schemas import stable_hash
from aibos.store import JsonlStore, read_json, write_json

FIELDS = ("topic", "trend", "date_discovered", "sources", "source_quality", "what_changed", "audience",
          "problem_solved", "teaching_angle", "demo_idea", "recording_plan", "script", "difficulty",
          "estimated_recording_time", "content_formats", "product_opportunity", "service_opportunity",
          "course_opportunity", "affiliate_opportunity", "performance", "lessons_learned")


class WorkflowError(ValueError):
    pass


def _wf() -> dict[str, Any]:
    return config.teaching().get("workflow", {})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def similarity(a: str, b: str) -> float:
    wa, wb = content_words(a), content_words(b)
    return len(wa & wb) / len(wa | wb) if wa and wb else 0.0


class TeachingDB:
    def __init__(self) -> None:
        self.dir = paths.sub("teaching")
        self.store = JsonlStore(self.dir / "opportunities.jsonl")

    # --- records -----------------------------------------------------------
    def all(self, status: str | None = None) -> list[dict[str, Any]]:
        items = self.store.all()
        return [i for i in items if status is None or i["status"] == status]

    def get(self, item_id: str) -> dict[str, Any]:
        for i in self.store.all():
            if i["id"] == item_id:
                return i
        raise KeyError(f"no teaching item {item_id!r} (see `aibos teaching list`)")

    def find_similar(self, topic: str, exclude_id: str | None = None) -> list[dict[str, Any]]:
        th = float(config.teaching().get("scoring", {}).get("duplicate_similarity", 0.6))
        return [i for i in self.store.all() if i["id"] != exclude_id and similarity(topic, i.get("topic", "")) >= th]

    def upsert(self, record: dict[str, Any], actor: str = "system") -> dict[str, Any]:
        items = self.store.all()
        record = dict(record)
        record.setdefault("id", "tch_" + stable_hash(record.get("topic"), record.get("date_discovered"))[:10])
        for f in FIELDS:
            record.setdefault(f, None)
        for i, existing in enumerate(items):
            if existing["id"] == record["id"]:
                merged = {**existing, **{k: v for k, v in record.items() if v is not None}}
                merged["updated_at"] = _now()
                items[i] = merged
                self.store.rewrite(items)
                return merged
        record.setdefault("status", "RESEARCHED")
        record["history"] = [{"to": record["status"], "by": actor, "at": _now(), "note": "created"}]
        record["created_at"] = record["updated_at"] = _now()
        items.append(record)
        self.store.rewrite(items)
        return record

    # --- workflow ----------------------------------------------------------
    def transition(self, item_id: str, to: str, actor: str, note: str = "", **fields: Any) -> dict[str, Any]:
        wf = _wf()
        states = wf["states"]
        to = to.upper()
        item = self.get(item_id)
        cur = item["status"]
        if cur in wf.get("terminal", []):
            raise WorkflowError(f"{item_id} is {cur}; no further transitions")
        if to == "REJECTED":
            pass
        elif to not in states:
            raise WorkflowError(f"unknown state {to}; states: {states + ['REJECTED']}")
        elif states.index(to) != states.index(cur) + 1:
            raise WorkflowError(f"{item_id}: {cur} -> {to} skips or reverses the workflow; next is "
                                f"{states[states.index(cur) + 1]}")
        is_human = actor != "system"
        if to in wf.get("human_only", []) and not is_human:
            raise WorkflowError(f"{to} is a human decision; the system cannot set it")
        if to in wf.get("system_only", []) and is_human:
            raise WorkflowError(f"{to} is set by the system after its work succeeds (e.g. `aibos record`)")
        if to == "PUBLISHED" and not fields.get("published_urls"):
            raise WorkflowError("PUBLISHED needs --url for where YOU published it (the system never publishes)")
        items = self.store.all()
        for i in items:
            if i["id"] == item_id:
                i.update({k: v for k, v in fields.items() if v is not None})
                i["status"] = to
                i["history"].append({"from": cur, "to": to, "by": actor, "at": _now(), "note": note})
                i["updated_at"] = _now()
                self.store.rewrite(items)
                return i
        raise KeyError(item_id)

    # --- learning loop -----------------------------------------------------
    def learning(self) -> dict[str, Any]:
        return read_json(self.dir / "learning.json", default={"category_performance": {}, "requested_topics": [],
                                                              "hook_findings": [], "updated_at": None})

    def save_learning(self, data: dict[str, Any]) -> None:
        data["updated_at"] = _now()
        write_json(self.dir / "learning.json", data)
