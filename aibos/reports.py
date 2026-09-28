"""Markdown reports: per-run chain report and the weekly strategy report (Part 38)."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from aibos import experiments as exp_mod
from aibos import integrations
from aibos.evidence import evidence_chain
from aibos.experiments import ExperimentStore
from aibos.memory import Memory
from aibos.schemas import Verification


def _val(v: Any) -> str:
    if isinstance(v, list):
        return "; ".join(_val(x) for x in v)
    if isinstance(v, dict):
        return ", ".join(f"{k}: {_val(x)}" for k, x in v.items())
    return str(v)


def render_items(items: list[Any], skip: tuple[str, ...] = ("produced_by",), title_key: str = "title") -> str:
    lines = []
    for it in items or []:
        if isinstance(it, dict):
            head = it.get(title_key) or it.get("name") or it.get("insight") or it.get("development") or ""
            lines.append(f"- **{head}**" if head else "-")
            for k, v in it.items():
                if k in skip or k in (title_key, "name") or v in (None, "", [], {}):
                    continue
                lines.append(f"  - *{k}*: {_val(v)}")
        else:
            lines.append(f"- {it}")
    return "\n".join(lines) or "_none_"


def run_report(ctx) -> str:
    b = ctx.board
    L: list[str] = []
    llm = [o for o in ctx.outputs if o.backend not in ("rule", "orchestrator")]
    rules = [o for o in ctx.outputs if o.backend == "rule"]
    L += [f"# Run report — {ctx.objective}", "",
          f"- **Run id:** `{ctx.run_id}`  ·  **Date:** {ctx.today}  ·  **Complexity:** {ctx.complexity}",
          f"- **Model backend:** {ctx.backend_name}",
          f"- **Team:** {len(llm)} model-backed agents + {len(rules)} deterministic checks "
          f"(out of {len(ctx.registry) if ctx.registry else '?'} registered)",
          f"- **Budget used:** {ctx.budget.spent_units} cost units, {ctx.budget.llm_calls} model calls, ${ctx.budget.usd:.4f}",
          f"- **Published externally:** nothing. Drafts are in the approval queue.", ""]

    L += ["## Plan", "", "| # | Stage | Orchestrator | Agents | Why |", "|---|---|---|---|---|"]
    for i, s in enumerate(ctx.stage_log, 1):
        L.append(f"| {i} | {s['stage']} | {s.get('orchestrator', '')} | {', '.join(s.get('agents', [])) or '—'} | {s.get('reason', '')} |")
    L.append("")

    L += ["## 1. RESEARCH", ""]
    for o in ctx.outputs:
        if o.agent_id.startswith(("research.", "business_intel.")):
            L += [f"**{o.agent_id}** ({o.status.value}; {o.provenance})", "", render_items(b.get("findings", [])), ""]
            if o.errors:
                L += [f"> {e}" for e in o.errors] + [""]
            break
    L += ["Sources captured:", ""]
    for s in ctx.sources.all():
        q = " — **QUARANTINED**" if s.source_id in ctx.quarantined_sources else ""
        L.append(f"- `{s.source_id}` [{s.title}]({s.url}) — {s.publisher}, {s.source_type}, published {s.published or 'unknown'}, "
                 f"retrieved {s.retrieved_at or 'unknown'} by {s.retrieved_by or 'unknown'}{q}")
    L.append("")

    L += ["## 2. VERIFY", "", "| Claim | Text | Verification | Kind | Confidence | Sources |", "|---|---|---|---|---|---|"]
    for c in ctx.claims:
        L.append(f"| {c.claim_id} | {c.text} | {c.verification.value} | {c.kind.value} | {c.confidence} | {', '.join(c.source_ids)} |")
    L.append("")
    weak = [c for c in ctx.claims if c.verification != Verification.SUPPORTED]
    if weak:
        L += ["Claims not fully supported (not used as facts):", ""]
        for c in weak:
            L.append(f"- **{c.claim_id}**: " + " | ".join(n for n in c.verification_notes if "PASS" not in n))
        L.append("")
    ver = ctx.verified_claims()
    if ver:
        L += ["### Evidence chain (CLAIM → SOURCE → EVIDENCE → CONFIDENCE → INTERPRETATION → DECISION)", ""]
        for c in ver[:3]:
            for link in evidence_chain(c, ctx.sources)[:2]:
                L += [f"- **CLAIM:** {link.claim}", f"  - **SOURCE:** {link.source}", f"  - **EVIDENCE:** “{link.evidence}”",
                      f"  - **CONFIDENCE:** {link.confidence}", f"  - **INTERPRETATION:** {link.interpretation}",
                      f"  - **DECISION:** {link.decision}"]
        L.append("")

    L += ["## 3. KNOWLEDGE", "", render_items(b.get("knowledge", []), skip=("produced_by", "evidence_chain")), ""]
    if b.get("open_questions"):
        L += ["Open questions:", "", render_items(b.get("open_questions"), title_key="text"), ""]

    L += ["## 4. TEACH", ""]
    for e in b.get("explanations", []) or []:
        L += [f"### {e.get('title', '')} ({e.get('level', '')})", "", e.get("text", ""), ""]
        if e.get("takeaways"):
            L += ["Takeaways:", ""] + [f"- {t}" for t in e["takeaways"]] + [""]
    if not b.get("explanations"):
        L += ["_no explanation produced_", ""]

    L += ["## 5. CONTENT", ""]
    if b.get("content_angles"):
        L += ["### Content angles", "", render_items(b["content_angles"]), ""]
    gate = b.get("quality_gate", {})
    for a in b.get("content", []) or []:
        g = gate.get(a.get("artifact_id"), {})
        L += [f"### {a.get('platform')} — {a.get('title', a.get('artifact_id'))}",
              f"_quality score {g.get('score', 'n/a')}; blocking issues: {len(g.get('blocking', []))}; "
              f"status: {'BLOCKED — ' + '; '.join(g.get('blocking', [])) if g.get('blocking') else 'PENDING HUMAN APPROVAL'}_", "",
              "```text", a.get("text", ""), "```", ""]
        if g.get("warnings"):
            L += ["Warnings: " + "; ".join(g["warnings"][:6]), ""]

    for key, title in (("opportunities", "6. OPPORTUNITY"), ("products", "7. PRODUCT"), ("revenue_models", "REVENUE MODELS")):
        L += [f"## {title}", "", render_items(b.get(key, [])), ""]

    L += ["## 8. EXPERIMENT", ""]
    for e in b.get("experiments", []) or []:
        rec = exp_mod.as_record(exp_mod.from_dict(e))
        L += [f"### {e.get('name', '')}", ""] + [f"- **{k}:** {v}" for k, v in rec.items()] + [""]
    if not b.get("experiments"):
        L += ["_no experiment designed_", ""]

    L += ["## 9. ANALYTICS PLAN", ""]
    plan = b.get("analytics_plan")
    if plan:
        for m in plan.get("content_metrics", []):
            L.append(f"- `{m['artifact_id']}` ({m['platform']}): {', '.join(m['metrics'])} — via {m['integration']} ({m['integration_status']})")
        for m in plan.get("experiment_metrics", []):
            L.append(f"- Experiment **{m['experiment']}**: metric `{m['metric']}`; success: {m['success']}; failure: {m['failure']}")
        L.append(f"- Data import path: `{plan.get('data_import')}`")
    else:
        L.append("_no analytics plan_")
    L.append("")

    if b.get("weekly_report_md"):
        L += [b["weekly_report_md"], ""]

    L += ["## Conflicts, escalations and security", ""]
    L += [f"- CONFLICT: {c['description']} → {c['resolution']}" for c in ctx.conflicts] or ["- no conflicts recorded"]
    L += [f"- ESCALATION: {e}" for e in ctx.escalations] or ["- no escalations"]
    L.append(f"- Security decision: {b.get('security_decision', 'not run')}; quarantined sources: {ctx.quarantined_sources or 'none'}")
    L.append("")

    L += ["## Agent run log", "", "| Agent | Status | Backend | Cost units | Seconds | Notes |", "|---|---|---|---|---|---|"]
    for o in ctx.outputs:
        note = (o.errors[0] if o.errors else (o.findings[0] if o.findings else ""))
        L.append(f"| {o.agent_id} | {o.status.value} | {o.backend} | {o.cost_units} | {o.duration_s:.3f} | {str(note)[:110].replace('|', '/')} |")
    L.append("")

    L += ["## Integration status", ""]
    for s in integrations.all_statuses():
        L.append(f"- **{s.name}**: {s.status} — {s.detail}")
    return "\n".join(L) + "\n"


def weekly_sections(ctx=None, days: int = 7) -> dict[str, list[str]]:
    mem = Memory()
    since = (date.today() - timedelta(days=days)).isoformat()
    recent = lambda rs: [r for r in rs if r.get("written_at", "")[:10] >= since]  # noqa: E731
    facts = recent(mem.read("global", kind="verified_fact"))
    opps = recent(mem.read("business", kind="opportunity"))
    open_q = recent(mem.read("project", kind="open_question"))
    lessons = recent(mem.read("agent_learning"))
    exps = ExperimentStore().all()
    board = ctx.board if ctx else {}
    analytics_out = board.get("analytics", [])
    no_data = lambda kw: [a for a in analytics_out if kw in a.get("agent_id", "")]  # noqa: E731

    def analytics_lines(kw: str) -> list[str]:
        rows = no_data(kw)
        if not rows:
            return ["NO DATA — no analytics were supplied; nothing was fabricated."]
        return [f"{r['agent_id']}: {_val({k: v for k, v in r.items() if k not in ('agent_id', 'produced_by')})}" for r in rows]

    sec = {
        "IMPORTANT TECHNOLOGY DEVELOPMENTS": [f"{f['content'].get('summary')} (confidence {f['content'].get('confidence')})" for f in facts][:10]
                                             or [c.text for c in (ctx.verified_claims() if ctx else [])][:10],
        "IMPORTANT AUDIENCE DEVELOPMENTS": [_val(i) for i in board.get("audience_insights", [])] or ["NO DATA — no audience data supplied."],
        "CONTENT PERFORMANCE": analytics_lines("content") + analytics_lines("social") + analytics_lines("email"),
        "PRODUCT EXPERIMENTS": [f"{e['name']} [{e['status']}]: {e['hypothesis']}" for e in exps] or ["none registered"],
        "REVENUE DATA": analytics_lines("revenue"),
        "CUSTOMER FEEDBACK": [_val(i) for i in board.get("audience_insights", []) if i.get("status") == "OBSERVED"] or ["NO DATA — no feedback files in data/feedback/."],
        "FAILED EXPERIMENTS": [f"{e['name']}: {e['interpretation']}" for e in exps if e["status"] == "COMPLETED" and "fail" in (e.get("result", "") + e.get("interpretation", "")).lower()] or ["none completed"],
        "SUCCESSFUL EXPERIMENTS": [f"{e['name']}: {e['interpretation']}" for e in exps if e["status"] == "COMPLETED" and "success" in (e.get("result", "") + e.get("interpretation", "")).lower()] or ["none completed"],
        "NEW OPPORTUNITIES": [f"{o['content'].get('title')} — {o['content'].get('status', 'HYPOTHESIS')}" for o in opps]
                             or [f"{o.get('title')} — HYPOTHESIS" for o in board.get("opportunities", [])] or ["none"],
        "RISKS": (list(ctx.escalations) if ctx else []) + [r for o in board.get("opportunities", []) for r in (o.get("risks") or [])][:8] or ["none recorded"],
        "OPEN QUESTIONS": [q["content"].get("text") for q in open_q][:10] or [q.get("text") for q in board.get("open_questions", [])] or ["none"],
        "RECOMMENDED EXPERIMENTS": [f"{e.get('name')}: {e.get('hypothesis')}" for e in board.get("experiments", [])]
                                   or [f"{e['name']}: {e['hypothesis']}" for e in exps if e["status"] == "DESIGNED"] or ["none"],
    }
    if lessons:
        sec["AGENT LEARNING"] = [_val(l["content"].get("lessons", l["content"])) for l in lessons][-5:]
    return sec


def weekly_report(ctx=None, title: str = "Weekly strategy report") -> str:
    L = [f"## {title} — week ending {datetime.now().date().isoformat()}", ""]
    for name, items in weekly_sections(ctx).items():
        L += [f"### {name}", ""] + [f"- {i}" for i in items] + [""]
    return "\n".join(L)
