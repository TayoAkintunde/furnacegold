"""Master and domain orchestrators (Parts 2, 24).

The master orchestrator does not do the work itself. It profiles the
objective, builds a plan with the smallest sufficient team, hands each stage to
the responsible domain orchestrator, verifies, resolves conflicts, escalates
uncertainty, and records learning.
"""
from __future__ import annotations

from typing import Any

from aibos import conflict, config
from aibos.backends import Backend, get_backend
from aibos.context import RunContext
from aibos.evidence import SourceStore, aggregate_verification
from aibos.registry import Registry
from aibos.reports import run_report, weekly_report
from aibos.runtime import AgentRunner
from aibos.schemas import AgentOutput, ClaimKind, RunStatus, Verification, to_jsonable
from aibos.selection import Plan, PlanStep, Selector
from aibos.store import write_json

# Stages whose work is meaningless without verified evidence when research was part of the plan.
EVIDENCE_DEPENDENT = {"TEACH", "CONTENT_STRATEGY", "CONTENT", "OPPORTUNITY", "PRODUCT", "REVENUE",
                      "EXPERIMENT", "CONTENT_ANGLES", "PLATFORM_CONTENT", "BEGINNER_EXPLANATION",
                      "INTERMEDIATE_EXPLANATION", "ADVANCED_EXPLANATION", "TUTORIAL", "PROJECT", "COURSE",
                      "WORKSHOP", "LEAD_MAGNET", "PRODUCT_OPPORTUNITIES", "CONTENT_OPPORTUNITIES",
                      "EDUCATION_OPPORTUNITIES", "IDENTIFY_OPPORTUNITIES", "PREPARE_DRAFTS",
                      "TRENDS", "MARKET", "COMPETITION", "SERVICE", "SAAS"}


def _available(ctx: RunContext, key: str) -> bool:
    if key == "claims":
        return bool(ctx.claims)
    if key == "artifacts":
        from aibos.rules import artifacts
        return bool(artifacts(ctx))
    return bool(ctx.get(key))


class DomainOrchestrator:
    """Level-1 orchestrator: runs one stage's agents in order and applies the stage hook."""

    def __init__(self, agent_id: str, registry: Registry, runner: AgentRunner):
        self.agent_id = agent_id
        self.reg = registry
        self.runner = runner

    def run_stage(self, step: PlanStep, ctx: RunContext) -> list[AgentOutput]:
        outs = []
        for aid in step.agents:
            spec = self.reg.get(aid)
            task = (f"{ctx.objective}\n\nSTAGE: {step.stage} — {step.description or spec.purpose}\n"
                    f"YOUR ROLE: {spec.name}: {spec.purpose}")
            outs.append(self.runner.run(spec, ctx, task))
        if step.post:
            getattr(Hooks, step.post)(ctx, step)
        return outs


class Hooks:
    """Stage post-processing performed by orchestrators (not by agents)."""

    @staticmethod
    def aggregate_verification(ctx: RunContext, step: PlanStep) -> None:
        aggregate_verification(ctx.claims, ctx.board.get("verification_reports", []), ctx.sources)
        ctx.conflicts.extend(conflict.from_verification(ctx))
        ver = ctx.verified_claims()
        if ctx.claims and not ver:
            ctx.escalations.append("VERIFY: no claim reached SUPPORTED; downstream stages will be skipped")
        elif len(ver) < len(ctx.claims):
            ctx.escalations.append(f"VERIFY: {len(ctx.claims) - len(ver)} of {len(ctx.claims)} claims not fully supported; excluded from factual use")

    @staticmethod
    def quality_gate(ctx: RunContext, step: PlanStep) -> None:
        gate: dict[str, dict[str, Any]] = {}
        for rep in ctx.board.get("quality_reports", []) or []:
            g = gate.setdefault(rep["artifact_id"], {"scores": [], "blocking": [], "warnings": []})
            g["scores"].append(rep["score"])
            for i in rep["issues"]:
                msg = f"{rep['agent_id'].split('.')[-1]}: {i['message']}"
                if i["severity"] == "BLOCKING":
                    g["blocking"].append(msg)
                elif i["severity"] == "WARN":
                    g["warnings"].append(msg)
        for aid, g in gate.items():
            g["score"] = round(sum(g["scores"]) / len(g["scores"]), 3) if g["scores"] else None
        for key in ("content", "explanations"):
            for a in ctx.board.get(key, []) or []:
                g = gate.get(a.get("artifact_id"))
                a["blocked"] = bool(g and g["blocking"])
        ctx.board["quality_gate"] = gate

    @staticmethod
    def approval_queue(ctx: RunContext, step: PlanStep) -> None:
        plats = config.platforms()
        queued = []
        for a in ctx.board.get("content", []) or []:
            g = (ctx.board.get("quality_gate") or {}).get(a.get("artifact_id"), {})
            item = ctx.approvals.submit(
                category="publish_content", title=f"Publish {a.get('platform')} draft: {a.get('title', '')}"[:120],
                payload={"artifact_id": a.get("artifact_id"), "platform": a.get("platform"), "text": a.get("text"),
                         "claim_ids": a.get("claim_ids"), "quality_score": g.get("score")},
                requested_by=a.get("produced_by", "?"), run_id=ctx.run_id,
                integration=plats.get(a.get("platform", ""), {}).get("integration"),
                blocked_reasons=g.get("blocking", []))
            queued.append(item["id"])
        for key in ("products", "experiments", "marketing_plans", "service_offers", "drafts", "sales_plans"):
            for it in ctx.board.get(key, []) or []:
                if isinstance(it, dict) and it.get("requires_approval"):
                    cat = it.get("approval_category", "high_risk_communication")
                    queued.append(ctx.approvals.submit(category=cat, title=f"{key}: {it.get('title') or it.get('name')}",
                                                       payload=it, requested_by=it.get("produced_by", "?"),
                                                       run_id=ctx.run_id)["id"])
        ctx.board["approval_items"] = queued

    @staticmethod
    def distribution_status(ctx: RunContext, step: PlanStep) -> None:
        from aibos import integrations
        plats = config.platforms()
        ctx.board["distribution"] = [
            {"artifact_id": a.get("artifact_id"), "platform": a.get("platform"),
             "status": "NOT PUBLISHED — awaiting human approval; integration "
                       + integrations.status(plats.get(a.get("platform", ""), {}).get("integration", "")).status}
            for a in ctx.board.get("content", []) or []]

    @staticmethod
    def launch_gate(ctx: RunContext, step: PlanStep) -> None:
        for p in ctx.board.get("products", []) or []:
            ctx.approvals.submit(category="major_product_launch", title=f"Launch: {p.get('title') or p.get('name')}",
                                 payload=p, requested_by=p.get("produced_by", "?"), run_id=ctx.run_id, risk="HIGH")

    @staticmethod
    def weekly_report(ctx: RunContext, step: PlanStep) -> None:
        md = weekly_report(ctx)
        ctx.board["weekly_report_md"] = md
        if ctx.persist:
            (ctx.run_dir / "weekly_report.md").write_text(md)


class MasterOrchestrator:
    agent_id = "orch.master"

    def __init__(self, registry: Registry | None = None, backend: Backend | None = None):
        self.reg = registry or Registry.load()
        self.backend = backend or get_backend("auto")
        self.runner = AgentRunner(self.backend)
        self.selector = Selector(self.reg)

    def plan(self, objective: str, complexity: str | None = None, pipeline: str | None = None) -> Plan:
        return self.selector.build_plan(objective, complexity, pipeline)

    def run(self, objective: str, sources: SourceStore | None = None, complexity: str | None = None,
            pipeline: str | None = None, persist: bool = True, board: dict[str, Any] | None = None,
            claims: list | None = None) -> RunContext:
        plan = self.plan(objective, complexity, pipeline)
        ctx = RunContext(objective=objective, sources=sources or SourceStore(), profile=plan.profile,
                         complexity=plan.profile.complexity, persist=persist, registry=self.reg,
                         backend_name=f"{self.backend.name}" + (f" ({getattr(self.backend, 'provenance', '')})"
                                                                if getattr(self.backend, "provenance", "") else ""))
        ctx.board.update(board or {})
        ctx.claims.extend(claims or [])          # seeded claims keep their verification status
        # Only notes that changed the plan (caps, unknown agents) are escalations; the rest are informational.
        ctx.escalations.extend(f"PLAN: {n}" for n in plan.notes if "below the typical" not in n)
        ctx.board["plan_notes"] = list(plan.notes)
        stage_names = [s.stage for s in plan.steps]
        research_planned = any(s in stage_names for s in ("RESEARCH", "TECHNOLOGY_DISCOVERY", "RESEARCH_NEW_DEVELOPMENTS"))
        if research_planned and not len(ctx.sources):
            ctx.escalations.append("RESEARCH: no captured sources supplied and web_search is NOT CONNECTED — "
                                   "add sources with `aibos sources add` or pass --sources")
        for step in plan.steps:
            entry = {"stage": step.stage, "orchestrator": step.orchestrator, "agents": list(step.agents),
                     "reason": step.reason, "selection_scores": step.selection_scores}
            if step.stage != "RESEARCH":
                self._evidence_guard(ctx)
            if research_planned and step.stage in EVIDENCE_DEPENDENT and not ctx.verified_claims():
                entry["status"] = "SKIPPED: INSUFFICIENT VERIFIED EVIDENCE"
                for aid in step.agents:
                    ctx.outputs.append(AgentOutput(aid, objective, RunStatus.SKIPPED, backend="orchestrator",
                                                   errors=["skipped: no verified claims to build on"]))
                ctx.stage_log.append(entry)
                continue
            missing = [r for r in step.requires if not _available(ctx, r)]
            if missing:
                entry["status"] = f"SKIPPED: nothing to process (no {', '.join(missing)})"
                ctx.stage_log.append(entry)
                continue
            ctx.stage_log.append(entry)
            if step.stage == "REPORT" and "weekly" in objective.lower():
                Hooks.weekly_report(ctx, step)      # objective asked for a weekly-style report
            orch = DomainOrchestrator(step.orchestrator, self.reg, self.runner)
            outs = orch.run_stage(step, ctx)
            entry["statuses"] = {o.agent_id: o.status.value for o in outs}
        if persist:
            self._save(ctx, plan)
            (ctx.run_dir / "report.md").write_text(run_report(ctx))   # final report incl. LEARN stage
        return ctx

    @staticmethod
    def _evidence_guard(ctx: RunContext) -> None:
        """Assumptions are never silently transformed into facts."""
        for c in ctx.claims:
            if c.kind == ClaimKind.FACT and c.verification != Verification.SUPPORTED:
                c.kind = ClaimKind.ASSUMPTION
                c.verification_notes.append("evidence-guard: labelled FACT without verification -> ASSUMPTION")

    @staticmethod
    def _save(ctx: RunContext, plan: Plan) -> None:
        write_json(ctx.run_dir / "run.json", {
            "run_id": ctx.run_id, "objective": ctx.objective, "profile": to_jsonable(plan.profile),
            "plan": [to_jsonable(s) for s in plan.steps], "plan_notes": plan.notes,
            "claims": to_jsonable(ctx.claims), "board": {k: v for k, v in to_jsonable(ctx.board).items() if not k.startswith("_")},
            "conflicts": ctx.conflicts, "escalations": ctx.escalations,
            "quarantined_sources": ctx.quarantined_sources,
            "budget": {"units": ctx.budget.spent_units, "llm_calls": ctx.budget.llm_calls, "usd": ctx.budget.usd},
            "outputs": [o.to_dict() for o in ctx.outputs],
        })
