"""Operational rules: experiments, automation, learning (Parts 20, 21, 31, 32, 40)."""
from __future__ import annotations

from collections import Counter

from aibos import integrations, performance
from aibos.experiments import ExperimentError, ExperimentStore, evaluate_ab, sample_size_per_variant, validate
from aibos.memory import MemoryError_
from aibos.paths import ROOT
from aibos.rules import out, rule
from aibos.schemas import RunStatus


@rule("ab_test")
def ab_test(ctx, spec):
    res = []
    for e in ctx.board.get("experiments", []) or []:
        d = e.get("data", {}) or {}
        row = {"experiment": e.get("name")}
        if "baseline_rate" in d and "mde_abs" in d:
            row["required_sample_per_variant"] = sample_size_per_variant(float(d["baseline_rate"]), float(d["mde_abs"]))
        if all(k in d for k in ("conv_a", "n_a", "conv_b", "n_b")):
            row.update(evaluate_ab(d["conv_a"], d["n_a"], d["conv_b"], d["n_b"]))
        else:
            row["result"] = "NOT RUN — no results supplied"
        res.append(row)
    return out(spec, ctx, findings=[str(r) for r in res] or ["no experiments"], data={"experiment_results": res}, confidence=1.0)


@rule("experiment_registrar")
def experiment_registrar(ctx, spec):
    exps = ctx.board.get("experiments", []) or []
    registered, problems = [], []
    store = ExperimentStore()
    for e in exps:
        p = validate(e)
        if p:
            problems.append(f"{e.get('name', '?')}: {'; '.join(p)}")
            e["registration"] = "REJECTED: " + "; ".join(p)
            continue
        if ctx.persist:
            try:
                x = store.register(dict(e, status="DESIGNED", result="NOT RUN"))
                e["experiment_id"] = x.experiment_id
            except ExperimentError as exc:
                problems.append(str(exc))
                continue
        e["registration"] = "PRE-REGISTERED (criteria fixed before running)"
        registered.append(e.get("name"))
    status = RunStatus.OK if exps and not problems else RunStatus.DEGRADED
    return out(spec, ctx, status=status, findings=[f"registered {registered}"] + problems,
               uncertainties=problems or ([] if exps else ["no experiments to register"]),
               files_changed=["data/experiments/experiments.jsonl"] if registered and ctx.persist else [],
               confidence=1.0)


@rule("integration_check")
def integration_check(ctx, spec):
    st = integrations.all_statuses()
    return out(spec, ctx, findings=[f"{s.name}: {s.status} ({s.detail})" for s in st],
               data={"integrations": {s.name: s.status for s in st}}, confidence=1.0)


@rule("schedule")
def schedule(ctx, spec):
    lines = [f"# m h dom mon dow  command  (NOT installed — add with `crontab -e` after review)",
             f"30 6 * * *  cd {ROOT} && python -m aibos teach-today",
             f"0 8 * * 1  cd {ROOT} && python -m aibos weekly"]
    return out(spec, ctx, findings=lines, data={"schedule": lines}, confidence=1.0,
               next_action="human installs the schedule; the system does not modify crontab")


@rule("report")
def report(ctx, spec):
    from aibos.reports import run_report
    md = run_report(ctx)
    path = ctx.run_dir / "report.md"
    path.write_text(md)
    return out(spec, ctx, findings=[f"report written ({len(md)} chars)"], data={"report_path": str(path)},
               files_changed=[str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)], confidence=1.0)


@rule("agent_evaluation")
def agent_evaluation(ctx, spec):
    scores = performance.evaluate(ctx.perf, int(spec.confidence_requirements.get("min_runs_for_judgement", 5)))
    flagged = {k: s.flags for k, s in scores.items() if s.flags}
    return out(spec, ctx, findings=[f"{len(scores)} agents with records; {len(flagged)} flagged"] +
               [f"{k}: {v}" for k, v in flagged.items()],
               data={"agent_scores": {k: s.as_row() for k, s in scores.items()}}, confidence=0.8)


@rule("agent_audit")
def agent_audit(ctx, spec):
    from aibos.audit import run_audit
    if ctx.registry is None:
        return out(spec, ctx, status=RunStatus.SKIPPED, findings=["registry not attached"])
    a = run_audit(ctx.registry, ctx.perf)
    summary = {k: (len(v) if isinstance(v, list) else v) for k, v in a.items()}
    return out(spec, ctx, findings=[f"{k}: {v}" for k, v in summary.items()], data={"agent_audit": a}, confidence=1.0)


@rule("improvement_proposals")
def improvement_proposals(ctx, spec):
    from aibos.audit import run_audit
    from aibos.improvement import propose
    if ctx.registry is None:
        return out(spec, ctx, status=RunStatus.SKIPPED, findings=["registry not attached"])
    props = propose(ctx.registry, ctx.board.get("agent_audit") or run_audit(ctx.registry, ctx.perf), ctx.perf)
    return out(spec, ctx, findings=[f"{len(props)} proposals PENDING_HUMAN_REVIEW (none applied)"],
               data={"proposals": props}, confidence=1.0)


@rule("correction_analysis")
def correction_analysis(ctx, spec):
    corr = ctx.perf.corrections.all()
    if not corr:
        return out(spec, ctx, status=RunStatus.DEGRADED, findings=["NO DATA: no human corrections recorded"])
    by_agent = Counter(c["agent_id"] for c in corr)
    themes = Counter(w for c in corr for w in c["note"].lower().split() if len(w) > 4)
    return out(spec, ctx, findings=[f"corrections by agent: {dict(by_agent)}", f"themes: {themes.most_common(8)}"],
               data={"correction_patterns": {"by_agent": dict(by_agent), "themes": themes.most_common(15)}}, confidence=0.7)


@rule("run_learning")
def run_learning(ctx, spec):
    statuses = Counter(o.status.value for o in ctx.outputs)
    blocked = [k for k, g in (ctx.board.get("quality_gate") or {}).items() if g.get("blocking")]
    lessons = []
    if statuses.get("NO_MODEL"):
        lessons.append(f"{statuses['NO_MODEL']} model-backed agents produced no output: connect a model backend")
    if blocked:
        lessons.append(f"drafts blocked by quality gate: {blocked}")
    unsupported = [c.claim_id for c in ctx.claims if c.verification.value in ("UNSUPPORTED", "CONTRADICTED")]
    if unsupported:
        lessons.append(f"claims failed verification: {unsupported} — research agents must quote sources verbatim")
    lessons.append(f"verified {len(ctx.verified_claims())}/{len(ctx.claims)} claims")
    errors = []
    if ctx.persist:
        try:
            ctx.memory.write("agent_learning", "run_summary",
                             {"run_id": ctx.run_id, "objective": ctx.objective, "statuses": dict(statuses),
                              "lessons": lessons}, tags=["run"], source=ctx.run_id)
            for o in ctx.board.get("opportunities", []) or []:
                ctx.memory.write("business", "opportunity",
                                 {"title": o.get("title"), "status": "HYPOTHESIS", "problem": o.get("problem"),
                                  "evidence_claim_ids": o.get("evidence_claim_ids"), "run_id": ctx.run_id},
                                 tags=["opportunity"], source=ctx.run_id)
            for a in ctx.board.get("content", []) or []:
                ctx.memory.write("content", "draft",
                                 {"artifact_id": a.get("artifact_id"), "platform": a.get("platform"),
                                  "title": a.get("title"), "run_id": ctx.run_id, "status": "PENDING_APPROVAL"},
                                 tags=[a.get("platform", "")], source=ctx.run_id)
            for e in ctx.board.get("experiments", []) or []:
                ctx.memory.write("experiment", "designed", {"name": e.get("name"), "hypothesis": e.get("hypothesis"),
                                                             "run_id": ctx.run_id}, source=ctx.run_id)
        except MemoryError_ as exc:
            errors.append(str(exc))
    return out(spec, ctx, findings=lessons, errors=errors, data={"lessons": lessons}, confidence=1.0)
