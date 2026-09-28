"""Human approval queue (Part 42). The system prepares actions; a human approves.

Approving an item does NOT pretend it was executed: execution requires a
connected integration, otherwise the item is marked NOT CONNECTED.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aibos import integrations, paths
from aibos.schemas import stable_hash
from aibos.store import JsonlStore

PENDING, APPROVED, REJECTED, EXECUTED, NOT_EXECUTED = (
    "PENDING", "APPROVED", "REJECTED", "EXECUTED", "NOT_EXECUTED")


class ApprovalQueue:
    def __init__(self) -> None:
        self.store = JsonlStore(paths.sub("approvals") / "queue.jsonl")

    def submit(self, *, category: str, title: str, payload: dict[str, Any], requested_by: str,
               run_id: str, integration: str | None = None, risk: str = "MEDIUM",
               blocked_reasons: list[str] | None = None) -> dict[str, Any]:
        item = {
            "id": "apr_" + stable_hash(category, title, payload, run_id),
            "category": category, "title": title, "payload": payload,
            "requested_by": requested_by, "run_id": run_id, "integration": integration,
            "integration_status": integrations.status(integration).status if integration else "N/A",
            "risk": risk, "status": PENDING, "blocked_reasons": blocked_reasons or [],
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "decided_at": None, "decided_by": None, "execution": None, "execution_note": None,
        }
        if item["id"] not in {i["id"] for i in self.store}:
            self.store.append(item)
        return item

    def list(self, status: str | None = PENDING) -> list[dict[str, Any]]:
        items = self.store.all()
        return [i for i in items if status is None or i["status"] == status]

    def decide(self, item_id: str, approve: bool, decided_by: str = "human") -> dict[str, Any]:
        items = self.store.all()
        for i in items:
            if i["id"] == item_id:
                if i["status"] != PENDING:
                    raise ValueError(f"{item_id} already {i['status']}")
                if approve and i.get("blocked_reasons"):
                    raise ValueError(f"{item_id} has blocking quality/security issues: {i['blocked_reasons']}")
                i["status"] = APPROVED if approve else REJECTED
                i["decided_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                i["decided_by"] = decided_by
                if approve:
                    self._execute(i)
                self.store.rewrite(items)
                return i
        raise KeyError(item_id)

    @staticmethod
    def _execute(item: dict[str, Any]) -> None:
        name = item.get("integration")
        st = integrations.status(name).status if name else integrations.NOT_CONNECTED
        # No publishing adapters are implemented; never claim execution.
        item["execution"] = NOT_EXECUTED
        item["execution_note"] = (f"Approved, but not executed: integration '{name}' is {st}. "
                                  "Export the payload and act on it manually, or implement the adapter.")
