"""Self-improvement (Part 32). Produces proposals only. Nothing here edits the
registry or prompts: every proposal is PENDING_HUMAN_REVIEW, and proposals for
critical agents are additionally marked `critical: true`."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from aibos import paths
from aibos.performance import PerformanceLog, evaluate
from aibos.registry import Registry
from aibos.schemas import stable_hash
from aibos.store import JsonlStore


def propose(reg: Registry, audit: dict[str, Any], log: PerformanceLog | None = None) -> list[dict[str, Any]]:
    log = log or PerformanceLog()
    scores = evaluate(log)
    proposals: list[dict[str, Any]] = []

    def add(kind: str, target: str, problem: str, suggestion: str, evidence: Any) -> None:
        critical = target in reg and reg.get(target).critical
        proposals.append({
            "proposal_id": "prop_" + stable_hash(kind, target, problem),
            "kind": kind, "target": target, "problem": problem, "suggestion": suggestion,
            "evidence": evidence, "critical": critical, "status": "PENDING_HUMAN_REVIEW",
            "auto_apply": False,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })

    for aid in audit.get("frequently_failing_agents", []):
        add("repeated_failure", aid, "failure rate > 20%", "inspect recent errors; tighten output contract or inputs",
            scores[aid].as_row())
    for aid in audit.get("poor_performing_agents", []):
        add("weak_agent", aid, "average quality < 0.6", "revise prompt template/focus; add examples", scores[aid].as_row())
    corr = defaultdict(list)
    for c in log.corrections:
        corr[c["agent_id"]].append(c["note"])
    for aid, notes in corr.items():
        if len(notes) >= 3:
            common = Counter(w for n in notes for w in n.lower().split() if len(w) > 4).most_common(5)
            add("frequent_corrections", aid, f"{len(notes)} human corrections", "update instructions to address recurring themes",
                {"themes": common, "examples": notes[:3]})
    for d in audit.get("duplicate_agents", []):
        add("duplicate_agents", ",".join(d["agents"]), d["reason"], d["recommendation"], d)
    for m in audit.get("missing_agents_or_capabilities", []):
        add("missing_capability", m.get("agent_id") or m.get("capability", "?"), m.get("reason", "referenced but missing"),
            "add/enable the agent or remove the reference", m)
    for o in audit.get("outdated_agents", []):
        add("outdated_prompt", o["agent_id"], o["reason"], "review and re-date instructions", o)
    # Inefficient workflows: agents whose outputs are frequently NO_MODEL/NOT_CONNECTED.
    for aid, s in scores.items():
        if s.runs >= 5 and s.degraded_runs / s.runs > 0.8:
            add("inefficient_workflow", aid, "mostly runs without a model/integration",
                "connect the backend/integration or remove the agent from default plans", s.as_row())

    store = JsonlStore(paths.sub("proposals") / "proposals.jsonl")
    existing = {p["proposal_id"] for p in store}
    for p in proposals:
        if p["proposal_id"] not in existing:
            store.append(p)
    return proposals
