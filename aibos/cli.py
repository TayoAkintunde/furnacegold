"""Command interface (Part 39). Usage: python -m aibos <command> [...]
Commands may be written with or without a leading slash (/research == research)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aibos import integrations
from aibos.backends import get_backend
from aibos.evidence import SourceStore, claim_from_dict, source_from_dict
from aibos.schemas import Source, stable_hash, to_jsonable

OBJECTIVES = {
    "research": "Research and verify recent developments in {topic}.",
    "content": "Research {topic}, verify it, and turn it into platform content.",
    "teach": "Research {topic}, verify it, and explain it to a {level}.",
    "opportunities": "Research {topic}, verify it, and identify business opportunities.",
    "product": "Research {topic}, verify it, identify opportunities, and design an MVP product with a validation experiment.",
    "service": "Research {topic}, verify it, and design a consulting service offer with a validation experiment.",
    "saas": "Research {topic}, verify it, and assess a SaaS product idea with a validation experiment.",
    "revenue": "Research {topic}, verify it, identify business opportunities and candidate revenue models.",
    "trends": "Research {topic} and identify trends.",
    "competitors": "Research {topic} and map competitors and alternatives.",
    "market": "Research {topic} and produce market research.",
}
DEMO_OBJECTIVE = ("Find an important recent development in AI, research it, verify it, explain it to a beginner, "
                  "turn it into several pieces of content, identify potential business opportunities, design one "
                  "validation experiment, and produce a weekly-style opportunity report.")


def _orch(args):
    from aibos.orchestrator import MasterOrchestrator
    return MasterOrchestrator(backend=get_backend(args.backend, args.responses))


def _sources(args) -> SourceStore:
    if getattr(args, "sources", None):
        return SourceStore.from_file(args.sources)
    return SourceStore.persistent()


def _print_run(ctx, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps({"run_id": ctx.run_id, "stages": ctx.stage_log,
                          "outputs": [{"agent": o.agent_id, "status": o.status.value} for o in ctx.outputs],
                          "escalations": ctx.escalations}, indent=2, default=str))
        return
    print(f"run {ctx.run_id}  complexity={ctx.complexity}  backend={ctx.backend_name}")
    for s in ctx.stage_log:
        st = s.get("status") or ", ".join(f"{a.split('.')[-1]}={v}" for a, v in (s.get("statuses") or {}).items()) or "—"
        print(f"  {s['stage']:<22} {st}")
    ver = ctx.verified_claims()
    print(f"claims verified: {len(ver)}/{len(ctx.claims)}   budget: {ctx.budget.spent_units} units, "
          f"{ctx.budget.llm_calls} model calls")
    for e in ctx.escalations:
        print(f"  ESCALATION: {e}")
    if ctx.persist:
        print(f"report: {ctx.run_dir / 'report.md'}")


def _run_objective(args, objective: str, pipeline: str | None = None, claims=None, board=None):
    ctx = _orch(args).run(objective, _sources(args), complexity=args.complexity, pipeline=pipeline,
                          persist=not args.no_persist, claims=claims, board=board)
    _print_run(ctx, args.json)
    return ctx


def cmd_objective(args):
    topic = " ".join(args.topic) or "AI"
    tmpl = OBJECTIVES[args.command]
    return _run_objective(args, tmpl.format(topic=topic, level=getattr(args, "level", "beginner")))


def cmd_run(args):
    return _run_objective(args, " ".join(args.objective))


def cmd_plan(args):
    from aibos.orchestrator import MasterOrchestrator
    plan = MasterOrchestrator(backend=get_backend("offline")).plan(" ".join(args.objective), args.complexity, args.pipeline)
    p = plan.profile
    print(f"TASK TYPE: {p.task_type}\nDOMAINS: {p.domains}\nRISK: {p.risk_level.value}\nCOMPLEXITY: {p.complexity}\n"
          f"OUTPUT: {p.output_type}\nTOOLS: {p.required_tools}")
    n_llm = 0
    for s in plan.steps:
        print(f"- {s.stage:<20} [{s.orchestrator}] {', '.join(s.agents) or '—'}\n    why: {s.reason}")
    from aibos.registry import Registry
    reg = Registry.load()
    n_llm = sum(1 for a in plan.agent_ids() if reg.get(a).executor == "llm")
    print(f"team: {n_llm} model-backed agents + {len(plan.agent_ids()) - n_llm} deterministic checks "
          f"(of {len(reg)} registered)")
    for n in plan.notes:
        print(f"note: {n}")


def cmd_pipeline(args):
    from aibos import config
    if not args.name:
        for k, v in config.pipelines().items():
            print(f"{k:<18} {v['description']}")
        return
    return _run_objective(args, " ".join(args.topic) or f"Run the {args.name} pipeline", pipeline=args.name)


def cmd_daily(args):
    return _run_objective(args, "Daily run: research new developments in " + (" ".join(args.topic) or "AI")
                          + ", verify, update knowledge, and prepare opportunities and drafts.", pipeline="daily")


def cmd_weekly(args):
    ctx = _run_objective(args, "Weekly strategy meeting report", pipeline="weekly")
    print("\n" + ctx.board.get("weekly_report_md", ""))


def cmd_analytics(args):
    return _run_objective(args, "Analyse content performance, analytics, trends and anomalies")


def cmd_repurpose(args):
    run = json.loads((Path(args.run_dir) / "run.json").read_text())
    claims = [claim_from_dict(c) for c in run["claims"]]
    board = {"knowledge": run["board"].get("knowledge", [])}
    platforms = " ".join(args.platforms) if args.platforms else ""
    return _run_objective(args, f"Repurpose verified knowledge into content {platforms}".strip(), claims=claims, board=board)


def cmd_agents(args):
    from aibos.registry import Registry
    reg = Registry.load()
    specs = reg.by_family(args.family) if args.family else reg.all()
    if args.json:
        print(json.dumps([s.to_dict() for s in specs], indent=2))
        return
    print(f"{len(reg)} agents in {len(reg.counts())} families")
    for fam, n in reg.counts().items():
        print(f"  {fam:<18} {n}")
    if args.family:
        for s in specs:
            print(f"  {s.agent_id:<42} {s.status.value:<12} {s.cost_class.value:<11} {s.executor}")


def cmd_agent_status(args):
    from aibos.performance import evaluate
    from aibos.registry import Registry
    reg = Registry.load()
    if args.agent_id:
        s = reg.get(args.agent_id)
        print(json.dumps(s.to_dict(), indent=2))
        sc = evaluate().get(args.agent_id)
        print("performance:", json.dumps(sc.as_row(), indent=2) if sc else "no runs recorded")
        return
    scores = evaluate()
    print(f"{'agent':<44}{'runs':>5}{'success':>9}{'quality':>9}{'cost':>7}  flags")
    for k, s in sorted(scores.items()):
        print(f"{k:<44}{s.runs:>5}{s.success_rate:>9}{str(s.avg_quality):>9}{s.total_cost_units:>7}  {','.join(s.flags)}")


def cmd_agent_test(args):
    """Run one agent against the fixture sources/claims to check it loads and behaves."""
    from aibos.context import RunContext
    from aibos.registry import Registry
    from aibos.runtime import AgentRunner
    reg = Registry.load()
    spec = reg.get(args.agent_id)
    fixture = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
    ctx = RunContext("agent test: " + spec.purpose, SourceStore.from_file(fixture / "sources.json"),
                     persist=False, registry=reg)
    ctx.add_claims(json.loads((fixture / "claims.json").read_text()), "fixture")
    ctx.board["content"] = json.loads((fixture / "content.json").read_text())
    o = AgentRunner(get_backend(args.backend, args.responses)).run(spec, ctx, "agent self-test")
    print(json.dumps(o.to_dict(), indent=2, default=str)[:6000])


def cmd_knowledge(args):
    from aibos.memory import Memory
    m = Memory()
    if args.query:
        for r in m.search(" ".join(args.query))[:20]:
            print(f"[{r['level']}/{r['kind']}] {json.dumps(r['content'], default=str)[:200]}")
    else:
        print(json.dumps(m.stats(), indent=2))


def cmd_experiment(args):
    from aibos.experiments import ExperimentStore, as_record, evaluate_ab, from_dict
    store = ExperimentStore()
    if args.action == "list":
        if not store.all():
            print("no experiments registered")
        for e in store.all():
            print(f"{e['experiment_id']}  [{e['status']}] {e['name']}")
    elif args.action == "show":
        e = next(e for e in store.all() if e["experiment_id"] == args.id)
        print(json.dumps(as_record(from_dict(e)), indent=2))
    elif args.action == "result":
        r = evaluate_ab(args.conv_a, args.n_a, args.conv_b, args.n_b)
        verdict = "SUCCESS" if r["significant"] and r["abs_lift"] > 0 else "FAIL/INCONCLUSIVE"
        e = store.record_result(args.id, f"{verdict}: {r}", r["interpretation"], args.next_action or "review",
                                data={"conv_a": args.conv_a, "n_a": args.n_a, "conv_b": args.conv_b, "n_b": args.n_b})
        print(json.dumps(as_record(from_dict(e)), indent=2))
    else:
        _run_objective(args, "Design a validation experiment for " + " ".join(args.topic or ["the latest opportunity"]))


def cmd_audit(args):
    from aibos.audit import run_audit
    from aibos.improvement import propose
    from aibos.registry import Registry
    reg = Registry.load()
    a = run_audit(reg)
    if args.json:
        print(json.dumps(a, indent=2, default=str))
    else:
        for k, v in a.items():
            if isinstance(v, list):
                print(f"{k}: {len(v)}")
                for x in v[:args.limit]:
                    print(f"    - {x}")
            else:
                print(f"{k}: {v}")
    if args.propose:
        props = propose(reg, a)
        print(f"\n{len(props)} improvement proposals written to data/proposals/ (PENDING_HUMAN_REVIEW, none applied)")


def cmd_sources(args):
    store = SourceStore.persistent()
    if args.action == "list":
        for s in store.all():
            print(f"{s.source_id}  {s.source_type:<13} {s.published or '?':<11} {s.publisher} — {s.title}")
        return
    if args.action == "import":
        new = SourceStore.from_file(args.file)
        for s in new.all():
            store.add(s)
        print(f"imported {len(new)} sources -> {store.save_persistent()}")
        return
    if args.url:
        st = integrations.status("http_fetch")
        try:
            got = integrations.fetch_url(args.url)
        except Exception as exc:  # report, never invent
            print(f"FAILED to fetch {args.url}: {exc}. Nothing was stored.")
            return 1
        text = got["text"]
        title = got["title"]
    else:
        text = Path(args.file).read_text()
        title = args.title or Path(args.file).name
    s = Source(source_id=args.id or "s_" + stable_hash(args.url or args.file)[:8], url=args.url or f"file://{args.file}",
               title=title, publisher=args.publisher or "unknown", source_type=args.type, published=args.published or "",
               retrieved_at=got["retrieved_at"] if args.url else "", retrieved_by="aibos sources add", text=text)
    store.add(s)
    print(f"stored {s.source_id} ({len(text)} chars) -> {store.save_persistent()}")


def cmd_approvals(args):
    from aibos.approval import ApprovalQueue
    q = ApprovalQueue()
    if args.action == "list":
        items = q.list(None if args.all else "PENDING")
        if not items:
            print("approval queue is empty")
        for i in items:
            blk = f" BLOCKED:{i['blocked_reasons']}" if i["blocked_reasons"] else ""
            print(f"{i['id']}  [{i['status']}] {i['category']:<22} {i['title'][:70]}  ({i['integration']}: {i['integration_status']}){blk}")
    elif args.action == "show":
        print(json.dumps(next(i for i in q.list(None) if i["id"] == args.id), indent=2))
    else:
        i = q.decide(args.id, approve=args.action == "approve", decided_by=args.by)
        print(json.dumps({k: i[k] for k in ("id", "status", "execution", "execution_note")}, indent=2))


def cmd_integrations(args):
    for s in integrations.all_statuses():
        print(f"{s.name:<18} {s.status:<20} {s.detail}   — {s.purpose}")


def cmd_correct(args):
    from aibos.performance import PerformanceLog
    PerformanceLog().record_correction(args.agent_id, args.run_id, " ".join(args.note), args.severity)
    print("correction recorded")


def cmd_demo(args):
    root = Path(__file__).resolve().parent.parent / "demo"
    args.sources = args.sources or str(root / "sources.json")
    args.responses = args.responses or str(root / "responses.json")
    args.complexity = args.complexity or "complex"
    return _run_objective(args, DEMO_OBJECTIVE)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="aibos", description="AI Business Operating System")
    sub = ap.add_subparsers(dest="command", required=True)

    def runopts(p):
        p.add_argument("--sources", help="JSON file of captured sources (default: data/sources/sources.json)")
        p.add_argument("--responses", help="scripted responses JSON (ScriptedBackend)")
        p.add_argument("--backend", default="auto", choices=["auto", "anthropic", "offline"])
        p.add_argument("--complexity", choices=["simple", "medium", "complex"])
        p.add_argument("--no-persist", action="store_true")
        p.add_argument("--json", action="store_true")
        return p

    for name in OBJECTIVES:
        p = runopts(sub.add_parser(name, help=OBJECTIVES[name].format(topic="<topic>", level="<level>")))
        p.add_argument("topic", nargs="*")
        if name == "teach":
            p.add_argument("--level", default="beginner", choices=["beginner", "intermediate", "advanced"])
        p.set_defaults(func=cmd_objective)
    p = runopts(sub.add_parser("run", help="run any objective through the master orchestrator"))
    p.add_argument("objective", nargs="+"); p.set_defaults(func=cmd_run)
    p = sub.add_parser("plan", help="show the agent team the orchestrator would select (no execution)")
    p.add_argument("objective", nargs="+"); p.add_argument("--complexity"); p.add_argument("--pipeline")
    p.set_defaults(func=cmd_plan)
    p = runopts(sub.add_parser("pipeline", help="list or run factory pipelines"))
    p.add_argument("name", nargs="?"); p.add_argument("topic", nargs="*"); p.set_defaults(func=cmd_pipeline)
    p = runopts(sub.add_parser("daily", help="daily autonomous workflow (Part 37)"))
    p.add_argument("topic", nargs="*"); p.set_defaults(func=cmd_daily)
    runopts(sub.add_parser("weekly", help="weekly strategy report (Part 38)")).set_defaults(func=cmd_weekly)
    runopts(sub.add_parser("analytics", help="analyse supplied metrics")).set_defaults(func=cmd_analytics)
    p = runopts(sub.add_parser("repurpose", help="turn a previous run's verified knowledge into content"))
    p.add_argument("run_dir"); p.add_argument("platforms", nargs="*"); p.set_defaults(func=cmd_repurpose)
    p = sub.add_parser("agents", help="list the agent registry")
    p.add_argument("--family"); p.add_argument("--json", action="store_true"); p.set_defaults(func=cmd_agents)
    p = sub.add_parser("agent-status", help="registry entry + performance")
    p.add_argument("agent_id", nargs="?"); p.set_defaults(func=cmd_agent_status)
    p = sub.add_parser("agent-test", help="run one agent against test fixtures")
    p.add_argument("agent_id"); p.add_argument("--backend", default="auto", choices=["auto", "anthropic", "offline"])
    p.add_argument("--responses"); p.set_defaults(func=cmd_agent_test)
    p = sub.add_parser("knowledge", help="memory stats or search")
    p.add_argument("query", nargs="*"); p.set_defaults(func=cmd_knowledge)
    p = runopts(sub.add_parser("experiment", help="list/show/result/design experiments"))
    p.add_argument("action", choices=["list", "show", "result", "design"])
    p.add_argument("--id"); p.add_argument("--conv-a", type=int); p.add_argument("--n-a", type=int)
    p.add_argument("--conv-b", type=int); p.add_argument("--n-b", type=int); p.add_argument("--next-action")
    p.add_argument("topic", nargs="*"); p.set_defaults(func=cmd_experiment)
    p = sub.add_parser("audit", help="agent audit (Part 40)")
    p.add_argument("--json", action="store_true"); p.add_argument("--propose", action="store_true")
    p.add_argument("--limit", type=int, default=8); p.set_defaults(func=cmd_audit)
    p = sub.add_parser("sources", help="manage captured sources")
    p.add_argument("action", choices=["list", "add", "import"]); p.add_argument("--url"); p.add_argument("--file")
    p.add_argument("--id"); p.add_argument("--title"); p.add_argument("--publisher"); p.add_argument("--published")
    p.add_argument("--type", default="unknown"); p.set_defaults(func=cmd_sources)
    p = sub.add_parser("approvals", help="human approval queue")
    p.add_argument("action", choices=["list", "show", "approve", "reject"]); p.add_argument("id", nargs="?")
    p.add_argument("--all", action="store_true"); p.add_argument("--by", default="human")
    p.set_defaults(func=cmd_approvals)
    sub.add_parser("integrations", help="integration status").set_defaults(func=cmd_integrations)
    p = sub.add_parser("correct", help="record a human correction to an agent's output")
    p.add_argument("agent_id"); p.add_argument("run_id"); p.add_argument("note", nargs="+")
    p.add_argument("--severity", default="minor"); p.set_defaults(func=cmd_correct)
    runopts(sub.add_parser("demo", help="run the Part 45 demonstration")).set_defaults(func=cmd_demo)
    return ap


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0].startswith("/"):
        argv[0] = argv[0][1:]
    args = build_parser().parse_args(argv)
    rc = args.func(args)
    return rc if isinstance(rc, int) else 0
