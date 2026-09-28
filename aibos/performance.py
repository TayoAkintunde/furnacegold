"""Agent performance tracking and evaluation (Part 31)."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from aibos import paths
from aibos.store import JsonlStore

SUCCESS = {"OK"}
NEUTRAL = {"NO_MODEL", "NOT_CONNECTED", "CREDENTIAL_REQUIRED", "AWAITING_APPROVAL", "SKIPPED"}


class PerformanceLog:
    def __init__(self) -> None:
        self.runs = JsonlStore(paths.sub("performance") / "agent_runs.jsonl")
        self.corrections = JsonlStore(paths.sub("performance") / "corrections.jsonl")

    def record(self, *, run_id: str, agent_id: str, task: str, status: str, duration_s: float,
               cost_units: float, quality: float | None, errors: list[str], backend: str,
               output_summary: str = "") -> None:
        self.runs.append({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run_id": run_id, "agent_id": agent_id, "task": task[:200], "status": status,
            "duration_s": round(duration_s, 4), "cost_units": cost_units, "quality": quality,
            "errors": errors, "backend": backend, "output": output_summary[:300],
        })

    def record_correction(self, agent_id: str, run_id: str, note: str, severity: str = "minor") -> None:
        """A human correction to an agent's output (the strongest learning signal)."""
        self.corrections.append({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "agent_id": agent_id, "run_id": run_id, "note": note, "severity": severity,
        })


@dataclass
class AgentScore:
    agent_id: str
    runs: int
    success_rate: float
    failure_rate: float
    avg_quality: float | None
    avg_duration_s: float
    total_cost_units: float
    corrections: int
    degraded_runs: int
    flags: list[str]

    def as_row(self) -> dict[str, Any]:
        return self.__dict__.copy()


def evaluate(log: PerformanceLog | None = None, min_runs: int = 5) -> dict[str, AgentScore]:
    log = log or PerformanceLog()
    by_agent: dict[str, list[dict]] = defaultdict(list)
    for r in log.runs:
        by_agent[r["agent_id"]].append(r)
    corrections: dict[str, int] = defaultdict(int)
    for c in log.corrections:
        corrections[c["agent_id"]] += 1
    scores = {}
    for agent_id in set(by_agent) | set(corrections):
        rs = by_agent.get(agent_id, [])
        n = len(rs)
        judged = [r for r in rs if r["status"] not in NEUTRAL]
        ok = sum(1 for r in judged if r["status"] in SUCCESS)
        failed = sum(1 for r in judged if r["status"] == "FAILED")
        quals = [r["quality"] for r in rs if r.get("quality") is not None]
        s = AgentScore(
            agent_id=agent_id, runs=n,
            success_rate=round(ok / len(judged), 3) if judged else 0.0,
            failure_rate=round(failed / len(judged), 3) if judged else 0.0,
            avg_quality=round(sum(quals) / len(quals), 3) if quals else None,
            avg_duration_s=round(sum(r["duration_s"] for r in rs) / n, 4) if n else 0.0,
            total_cost_units=sum(r.get("cost_units", 0) for r in rs),
            corrections=corrections.get(agent_id, 0),
            degraded_runs=sum(1 for r in rs if r["status"] in NEUTRAL),
            flags=[],
        )
        if n >= min_runs:
            if s.failure_rate > 0.2:
                s.flags.append("FREQUENTLY_FAILING")
            if s.avg_quality is not None and s.avg_quality < 0.6:
                s.flags.append("LOW_QUALITY")
        if s.corrections >= 3 or (n and s.corrections / max(n, 1) > 0.3):
            s.flags.append("FREQUENT_CORRECTIONS")
        scores[agent_id] = s
    return scores
