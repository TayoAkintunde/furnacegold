"""Task profiling and agent selection (Part 25).

The profiler derives TASK TYPE, DOMAIN, REQUIRED EXPERTISE, REQUIRED TOOLS,
RISK LEVEL, COMPLEXITY and OUTPUT TYPE from the objective. The selector then
builds a plan of stages and picks the smallest sufficient set of agents for
each stage. Deterministic, explainable, and cheap (no model call).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aibos import config
from aibos.registry import Registry
from aibos.schemas import AgentSpec, RiskLevel, TaskProfile

MAJOR_STAGE_TYPE = {"RESEARCH": "research", "TEACH": "education", "CONTENT": "content",
                    "OPPORTUNITY": "opportunity", "PRODUCT": "product", "REVENUE": "revenue",
                    "EXPERIMENT": "experiment", "ANALYTICS": "analytics", "CONTENT_STRATEGY": "content"}
HIGH_RISK = re.compile(r"\b(publish|post it|launch|pay|payment|advertis|ads\b|contract|sign|delete|deploy|production|email (all|our) )", re.I)
MEDIUM_RISK = re.compile(r"\b(content|product|revenue|pricing|offer|customer|outreach|sales)\b", re.I)
LEVELS = ("beginner", "intermediate", "advanced")


@dataclass
class PlanStep:
    stage: str
    orchestrator: str
    agents: list[str]
    reason: str
    description: str = ""
    post: str | None = None
    requires: list[str] = field(default_factory=list)
    selection_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class Plan:
    profile: TaskProfile
    steps: list[PlanStep]
    notes: list[str] = field(default_factory=list)

    def agent_ids(self) -> list[str]:
        return [a for s in self.steps for a in s.agents]


def _intent_hit(objective: str, intent: str) -> bool:
    # whole-word match (plural allowed) so short keywords like "ide" don't match "identify"
    pattern = r"(?<![a-z0-9])" + re.escape(intent.lower()) + r"(?:s|es)?(?![a-z0-9])"
    return re.search(pattern, objective.lower()) is not None


def detect_stages(objective: str) -> tuple[list[str], dict[str, str]]:
    lib = config.stages()
    order, stages = lib["order"], lib["stages"]
    chosen: dict[str, str] = {}
    for name, st in stages.items():
        hits = [i for i in st.get("intents", []) if _intent_hit(objective, i)]
        if hits:
            chosen[name] = f"objective mentions {hits[:3]}"
    changed = True
    while changed:
        changed = False
        for name in list(chosen):
            for imp in stages[name].get("implies", []):
                if imp not in chosen:
                    chosen[imp] = f"required by {name}"
                    changed = True
    for name, st in stages.items():
        if st.get("always"):
            chosen.setdefault(name, "always runs (safety/reporting)")
    return [s for s in order if s in chosen], chosen


def profile(objective: str, complexity: str | None = None) -> TaskProfile:
    stages, _ = detect_stages(objective)
    lib = config.stages()["stages"]
    major = [s for s in stages if s in MAJOR_STAGE_TYPE]
    if complexity is None:
        n = len({MAJOR_STAGE_TYPE[s] for s in major})
        complexity = "simple" if n <= 1 else "medium" if n <= 3 else "complex"
    types = list(dict.fromkeys(MAJOR_STAGE_TYPE[s] for s in major))
    task_type = types[0] if len(types) == 1 else ("multi_stage:" + "+".join(types) if types else "general")
    domains = list(dict.fromkeys(lib[s]["orchestrator"].split(".")[-1] for s in stages))
    risk = RiskLevel.HIGH if HIGH_RISK.search(objective) else RiskLevel.MEDIUM if MEDIUM_RISK.search(objective) else RiskLevel.LOW
    tools = ["source_store"] + (["web_search"] if "RESEARCH" in stages else []) + (["platform_rules"] if "CONTENT" in stages else [])
    output = ("report" if re.search(r"report|brief|summary", objective, re.I) else
              "content_drafts" if "CONTENT" in stages else "analysis")
    words = [w for w in re.findall(r"[a-z][a-z\-]+", objective.lower()) if len(w) > 3]
    return TaskProfile(objective=objective, task_type=task_type, domains=domains,
                       required_expertise=sorted(set(words))[:25], required_tools=tools, risk_level=risk,
                       complexity=complexity, output_type=output, stages=stages, keywords=words)


def score_agent(spec: AgentSpec, objective: str) -> float:
    obj = objective.lower()
    kw = sum(2.0 for k in spec.keywords if _intent_hit(obj, k))
    name = sum(1.0 for w in re.findall(r"[a-z]+", spec.name.lower()) if len(w) > 3 and w not in ("agent", "researcher", "research", "analyst", "strategist") and _intent_hit(obj, w))
    return kw + name + spec.priority / 10.0


class Selector:
    def __init__(self, registry: Registry):
        self.reg = registry

    def _pool(self, pool: dict[str, Any]) -> list[AgentSpec]:
        cands = self.reg.usable()
        if pool.get("families"):
            cands = [a for a in cands if a.family in pool["families"]]
        if pool.get("capability"):
            cands = [a for a in cands if pool["capability"] in a.capabilities]
        return cands

    def select_stage(self, name: str, st: dict[str, Any], prof: TaskProfile) -> tuple[list[str], dict[str, float], str]:
        cx = prof.complexity
        if "agents" in st:
            ag = st["agents"]
            chosen = ag.get(cx, ag.get("medium", [])) if isinstance(ag, dict) else ag
            return [a for a in chosen if a in self.reg], {}, f"fixed stage team ({cx})"
        count = (st.get("count") or {}).get(cx, 1)
        cands = self._pool(st.get("pool", {}))
        obj = prof.objective
        if st.get("level_select"):
            wanted = [lv for lv in LEVELS if lv in obj.lower()] or ["beginner"]
            picked = [a.agent_id for lv in wanted for a in cands if a.params.get("level") == lv]
            return picked, {}, f"learner level(s) requested: {wanted}"
        if st.get("platform_select"):
            # keywords name the platform (linkedin, x, tiktok); params.format_keywords name a format
            # (thread, carousel). A format variant is chosen only when its format is named, and it
            # then replaces the plain variant of the same platform group.
            named = [a for a in cands
                     if any(_intent_hit(obj, k) for k in a.keywords)
                     and (not a.params.get("format_keywords")
                          or any(_intent_hit(obj, f) for f in a.params["format_keywords"]))]
            formatted = {a.params.get("group") for a in named if a.params.get("format_keywords")}
            named = [a for a in named if a.params.get("format_keywords") or a.params.get("group") not in formatted]
            if named:
                named.sort(key=lambda a: -score_agent(a, obj))
                return [a.agent_id for a in named[:max(count, len(named))]], {}, "platforms named in objective"
            defaults = config.settings().get("default_platforms", [])
            picked = [a.agent_id for p in defaults for a in cands if a.params.get("platform") == p][:count]
            return picked, {}, f"default platforms {defaults[:count]} (none named)"
        scored = sorted(((score_agent(a, obj), a) for a in cands), key=lambda x: (-x[0], x[1].agent_id))
        # The best candidate always runs; extra agents are added only if they match the objective
        # (a score above their priority baseline) — never to fill a quota.
        top = scored[:1] + [(sc, a) for sc, a in scored[1:count] if sc > a.priority / 10.0]
        return [a.agent_id for _, a in top], {a.agent_id: round(s, 2) for s, a in scored[:5]}, \
            f"top {len(top)} of {len(cands)} candidates by keyword/priority score (max {count})"

    def build_plan(self, objective: str, complexity: str | None = None, pipeline: str | None = None) -> Plan:
        prof = profile(objective, complexity)
        lib = config.stages()["stages"]
        steps: list[PlanStep] = []
        notes: list[str] = []
        if pipeline:
            p = config.pipelines()[pipeline]
            if complexity is None:
                prof.complexity = p.get("complexity", prof.complexity)
            prof.stages = [s["name"] for s in p["steps"]]
            prof.task_type = f"pipeline:{pipeline}"
            for s in p["steps"]:
                if s.get("ref"):
                    st = lib[s["ref"]]
                    agents, scores, why = self.select_stage(s["ref"], st, prof)
                    steps.append(PlanStep(s["name"], st["orchestrator"], agents, f"{s['ref']}: {why}",
                                          st.get("description", ""), s.get("post", st.get("post")),
                                          st.get("requires", []), scores))
                else:
                    agents = [a for a in s.get("agents", []) if a in self.reg]
                    missing = [a for a in s.get("agents", []) if a not in self.reg]
                    if missing:
                        notes.append(f"step {s['name']}: unknown agents {missing}")
                    orch = self.reg.get(agents[0]).domain if agents else "master"
                    steps.append(PlanStep(s["name"], f"orch.{orch}" if f"orch.{orch}" in self.reg else "orch.master",
                                          agents, "pipeline step", "", s.get("post")))
        else:
            stages, reasons = detect_stages(objective)
            for name in stages:
                st = lib[name]
                agents, scores, why = self.select_stage(name, st, prof)
                steps.append(PlanStep(name, st["orchestrator"], agents, f"{reasons[name]}; {why}",
                                      st.get("description", ""), st.get("post"), st.get("requires", []), scores))
        self._enforce_team_size(prof, steps, notes)
        return Plan(prof, steps, notes)

    def _enforce_team_size(self, prof: TaskProfile, steps: list[PlanStep], notes: list[str]) -> None:
        bounds = config.settings().get("team_size", {}).get(prof.complexity, {"min": 1, "max": 20})
        llm = [a for s in steps for a in s.agents if self.reg.get(a).executor == "llm"]
        while len(llm) > bounds["max"]:
            # drop the lowest-priority model agent from the largest stage
            big = max(steps, key=lambda s: sum(self.reg.get(a).executor == "llm" for a in s.agents))
            victims = sorted((a for a in big.agents if self.reg.get(a).executor == "llm"),
                             key=lambda a: self.reg.get(a).priority)
            big.agents.remove(victims[0])
            notes.append(f"team cap {bounds['max']}: dropped {victims[0]} from {big.stage}")
            llm = [a for s in steps for a in s.agents if self.reg.get(a).executor == "llm"]
        if len(llm) < bounds["min"]:
            notes.append(f"{len(llm)} model agents is below the typical {prof.complexity} range "
                         f"({bounds['min']}-{bounds['max']}); not padded — smallest sufficient team")
        rule_cap = int(config.settings().get("max_rule_checks_per_run", 30))
        rules = [a for s in steps for a in s.agents if self.reg.get(a).executor != "llm"]
        if len(rules) > rule_cap:
            notes.append(f"{len(rules)} deterministic checks exceeds cap {rule_cap}")
