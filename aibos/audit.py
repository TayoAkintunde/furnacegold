"""Agent audit (Part 40) — structural checks on the registry plus behavioural
checks from the performance log."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from itertools import combinations
from typing import Any

from aibos import config
from aibos.paths import PROMPTS_DIR
from aibos.performance import PerformanceLog, evaluate
from aibos.registry import Registry
from aibos.schemas import AgentStatus, CostClass

ROLE_WORDS = {"agent", "analyst", "strategist", "researcher", "evaluator", "detector", "verifier",
              "architect", "manager", "creator", "designer", "builder", "specialist", "the", "and", "of",
              "a", "-", "service", "revenue", "sales", "analytics"}


def _core(name: str) -> set[str]:
    return {w for w in name.lower().replace("-", " ").replace("/", " ").split() if w not in ROLE_WORDS}


def referenced_agents() -> dict[str, list[str]]:
    refs: dict[str, list[str]] = defaultdict(list)
    for sname, st in config.stages().get("stages", {}).items():
        ag = st.get("agents", [])
        lists = ag.values() if isinstance(ag, dict) else [ag]
        for lst in lists:
            for a in lst:
                refs[a].append(f"stage:{sname}")
    for pname, p in config.pipelines().items():
        for step in p.get("steps", []):
            for a in step.get("agents", []) or []:
                refs[a].append(f"pipeline:{pname}")
    for rname, r in config.revenue_streams().items():
        for a in r.get("agents", []):
            refs[a].append(f"revenue_stream:{rname}")
    return refs


def run_audit(reg: Registry, log: PerformanceLog | None = None, review_days: int = 180) -> dict[str, Any]:
    from aibos.rules import RULES  # local import to avoid cycles
    log = log or PerformanceLog()
    scores = evaluate(log)
    runs = defaultdict(int)
    for r in log.runs:
        runs[r["agent_id"]] += 1
    specialists = [a for a in reg.all() if a.executor != "orchestrator"]

    unused = sorted(a.agent_id for a in specialists if runs[a.agent_id] == 0)

    duplicates = []
    for a, b in combinations(specialists, 2):
        ca, cb = _core(a.name), _core(b.name)
        if ca and cb and len(ca & cb) / len(ca | cb) >= 0.99 and a.family != b.family:
            duplicates.append({"agents": [a.agent_id, b.agent_id], "reason": f"same core name {sorted(ca)}",
                               "recommendation": "merge or document the distinct scope"})

    poor = sorted(k for k, s in scores.items() if "LOW_QUALITY" in s.flags)
    failing = sorted(k for k, s in scores.items() if "FREQUENTLY_FAILING" in s.flags)
    corrected = sorted(k for k, s in scores.items() if "FREQUENT_CORRECTIONS" in s.flags)

    today = date.today()
    outdated, never_reviewed = [], 0
    for a in reg.all():
        if a.status == AgentStatus.DEPRECATED:
            outdated.append({"agent_id": a.agent_id, "reason": "DEPRECATED"})
        elif a.last_reviewed:
            try:
                age = (today - datetime.fromisoformat(a.last_reviewed).date()).days
                if age > review_days:
                    outdated.append({"agent_id": a.agent_id, "reason": f"instructions last reviewed {age} days ago"})
            except ValueError:
                outdated.append({"agent_id": a.agent_id, "reason": "unparseable last_reviewed"})
        else:
            never_reviewed += 1

    missing = []
    for ref, where in referenced_agents().items():
        if ref not in reg:
            missing.append({"agent_id": ref, "referenced_by": where})
        elif reg.get(ref).status in (AgentStatus.DISABLED, AgentStatus.DEPRECATED):
            missing.append({"agent_id": ref, "referenced_by": where, "reason": f"status {reg.get(ref).status.value}"})
    for sname, st in config.stages().get("stages", {}).items():
        cap = (st.get("pool") or {}).get("capability")
        if cap and not reg.with_capability(cap):
            missing.append({"capability": cap, "referenced_by": [f"stage:{sname}"]})
    for a in reg.all():
        if a.is_rule and a.rule_name not in RULES:
            missing.append({"agent_id": a.agent_id, "reason": f"rule '{a.rule_name}' not implemented"})
        if a.executor == "llm" and not (PROMPTS_DIR / f"{a.prompt_template}.md").exists():
            missing.append({"agent_id": a.agent_id, "reason": f"prompt template '{a.prompt_template}' missing"})
        plat = a.params.get("platform")
        if plat and plat not in config.platforms():
            missing.append({"agent_id": a.agent_id, "reason": f"platform '{plat}' not in config/platforms.yaml"})

    expensive = sorted(({"agent_id": k, "cost_units": s.total_cost_units} for k, s in scores.items()
                        if s.total_cost_units > 0), key=lambda x: -x["cost_units"])[:10]
    high_cost_count = sum(1 for a in reg.all() if a.cost_class == CostClass.HIGH_COST and a.executor == "llm")

    needs_review = sorted(set(
        [a.agent_id for a in reg.all() if a.status == AgentStatus.EXPERIMENTAL] + corrected + failing + poor))

    return {
        "total_agents": len(reg), "specialists": len(specialists),
        "unused_agents": unused, "duplicate_agents": duplicates, "poor_performing_agents": poor,
        "outdated_agents": outdated, "never_reviewed_count": never_reviewed,
        "missing_agents_or_capabilities": missing, "expensive_agents": expensive,
        "high_cost_llm_agents": high_cost_count, "frequently_failing_agents": failing,
        "agents_needing_human_review": needs_review,
    }
