"""Run context: the shared blackboard agents read from and write to."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aibos import paths
from aibos.approval import ApprovalQueue
from aibos.cost import Budget
from aibos.evidence import SourceStore, claim_from_dict
from aibos.memory import Memory
from aibos.performance import PerformanceLog
from aibos.schemas import AgentOutput, Claim, ClaimKind, TaskProfile, Verification


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:6]


@dataclass
class RunContext:
    objective: str
    sources: SourceStore
    run_id: str = field(default_factory=new_run_id)
    profile: TaskProfile | None = None
    complexity: str = "medium"
    board: dict[str, Any] = field(default_factory=dict)
    claims: list[Claim] = field(default_factory=list)
    outputs: list[AgentOutput] = field(default_factory=list)
    stage_log: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    escalations: list[str] = field(default_factory=list)
    quarantined_sources: list[str] = field(default_factory=list)
    budget: Budget = field(default_factory=Budget.from_settings)
    perf: PerformanceLog = field(default_factory=PerformanceLog)
    memory: Memory = field(default_factory=Memory)
    approvals: ApprovalQueue = field(default_factory=ApprovalQueue)
    persist: bool = True
    registry: Any = None
    backend_name: str = ""
    today: str = field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())

    @property
    def run_dir(self) -> Path:
        d = paths.sub("runs") / self.run_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    # --- blackboard -----------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        if key == "objective":
            return self.objective
        if key == "claims":
            return self.claims
        if key == "sources":
            return self.sources.all()
        return self.board.get(key, default)

    def merge(self, key: str, value: Any, agent_id: str) -> None:
        if key == "claims":
            self.add_claims(value, agent_id)
            return
        cur = self.board.get(key)
        if isinstance(value, list):
            tagged = [dict(v, produced_by=v.get("produced_by", agent_id)) if isinstance(v, dict) else v
                      for v in value]
            self.board[key] = (cur or []) + tagged if isinstance(cur, list) or cur is None else tagged
        elif isinstance(value, dict) and isinstance(cur, dict):
            cur.update(value)
        else:
            self.board[key] = value

    def add_claims(self, items: list[Any], agent_id: str) -> None:
        existing = {c.claim_id for c in self.claims}
        for i, item in enumerate(items or []):
            d = dict(item) if isinstance(item, dict) else {"text": str(item)}
            d.setdefault("claim_id", f"c{len(self.claims) + 1}")
            if d["claim_id"] in existing:
                d["claim_id"] = f"{d['claim_id']}_{agent_id.split('.')[-1]}_{i}"
            # Agents cannot self-certify: incoming claims always start UNVERIFIED.
            d["verification"] = Verification.UNVERIFIED.value
            d.setdefault("kind", ClaimKind.ASSUMPTION.value)
            if isinstance(d.get("quotes"), str):
                d["quotes"] = [d["quotes"]]
            c = claim_from_dict(d)
            self.claims.append(c)
            existing.add(c.claim_id)

    def verified_claims(self) -> list[Claim]:
        return [c for c in self.claims if c.verification == Verification.SUPPORTED]

    def context_for(self, keys: list[str]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k in keys:
            if k == "sources":
                out[k] = [{"source_id": s.source_id, "title": s.title, "publisher": s.publisher,
                           "url": s.url, "published": s.published, "source_type": s.source_type,
                           "text": s.text} for s in self.sources.all()
                          if s.source_id not in self.quarantined_sources]
            elif k == "claims":
                out[k] = [{"claim_id": c.claim_id, "text": c.text, "kind": c.kind.value,
                           "verification": c.verification.value, "confidence": c.confidence,
                           "source_ids": c.source_ids} for c in self.claims]
            else:
                v = self.get(k)
                if v not in (None, [], {}):
                    out[k] = v
        return out
