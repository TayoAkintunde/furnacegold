"""Persistence hook for the teaching pipelines: writes the content database, advances the workflow
(system transitions only), and queues content for the owner's approval. Never publishes."""
from __future__ import annotations

from typing import Any

from aibos import config
from aibos.evidence import SOURCE_TIER
from aibos.schemas import Verification, to_jsonable
from aibos.teaching_db import TeachingDB, WorkflowError

BIZ_FIELDS = {"product_opportunity": ("digital_product", "saas"),
              "service_opportunity": ("consulting", "automation_service", "implementation_service"),
              "course_opportunity": ("course", "workshop"),
              "affiliate_opportunity": ("affiliate",)}


def _gate_blocking(ctx, prefix_ids: list[str]) -> list[str]:
    gate = ctx.board.get("quality_gate") or {}
    return [f"{aid}: {b}" for aid in prefix_ids for b in (gate.get(aid) or {}).get("blocking", [])]


def _biz(ctx) -> dict[str, Any]:
    biz = ctx.board.get("teaching_business") or []
    out = {}
    for field, types in BIZ_FIELDS.items():
        genuine = [x for x in biz if x.get("type") in types and x.get("genuine")]
        out[field] = [{"type": x["type"], "reasoning": x.get("reasoning"), "cheapest_test": x.get("cheapest_test")}
                      for x in genuine] or "none genuine"
    return out


def _claims_for(ctx, ids: list[str]) -> list[dict[str, Any]]:
    return [to_jsonable(c) for c in ctx.claims if c.claim_id in ids]


def _sources_for(ctx, ids: list[str]) -> tuple[list[dict], dict[str, float]]:
    sids = sorted({sid for c in ctx.claims if c.claim_id in ids for sid in c.source_ids})
    srcs = [to_jsonable(s) for sid in sids if (s := ctx.sources.get(sid))]
    return srcs, {s["source_id"]: SOURCE_TIER.get(s["source_type"], 0.2) for s in srcs}


def persist(ctx) -> None:
    if not ctx.persist:
        return
    mode = ctx.board.get("teaching_mode", "teach_today")
    {"teach_today": _teach_today, "record": _record, "content": _content}.get(mode, lambda c: None)(ctx)


def _teach_today(ctx) -> None:
    db = TeachingDB()
    opps = {o.get("opp_id"): o for o in ctx.board.get("teaching_opportunities", []) or []}
    sel = (ctx.board.get("teaching_selection") or [None])[0]
    ids: dict[str, str] = {}
    for row in ctx.board.get("teaching_scores", []) or []:
        if any(r.startswith("already covered") for r in row["reasons"]):
            continue                                   # do not duplicate an existing item
        o = opps.get(row["opp_id"], {})
        claim_ids = o.get("claim_ids") or []
        verified = [cid for cid in claim_ids if any(c.claim_id == cid and c.verification == Verification.SUPPORTED
                                                     for c in ctx.claims)]
        srcs, quality = _sources_for(ctx, verified or claim_ids)
        rec: dict[str, Any] = {
            "topic": o.get("topic"), "trend": o.get("trend"), "category": o.get("category"),
            "date_discovered": ctx.today, "sources": srcs, "source_quality": quality,
            "what_changed": o.get("what_changed"), "audience": o.get("who_should_care"),
            "problem_solved": o.get("problem_solved"), "teaching_angle": o.get("teaching_angle"),
            "demo_idea": (o.get("demonstration") or {}).get("how"), "difficulty": o.get("difficulty"),
            "value_answers": o.get("value_answers"), "claims": _claims_for(ctx, verified),
            "score": row["total"], "score_breakdown": row["breakdown"], "score_notes": row["notes"],
            "gate_reasons": row["reasons"], "run_id": ctx.run_id,
            "recommended": bool(sel and sel.get("opp_id") == row["opp_id"]),
        }
        if row["rejected"]:
            rec["status"] = "REJECTED"
        if rec["recommended"]:
            plan = next((p for p in ctx.board.get("recording_plans", []) or [] if p.get("opp_id") == row["opp_id"]), None)
            script = next((s for s in ctx.board.get("scripts", []) or [] if s.get("opp_id") == row["opp_id"]), None)
            rec.update({"recording_plan": plan, "script": script,
                        "estimated_recording_time": (plan or {}).get("estimated_recording_minutes"),
                        "content_formats": ctx.board.get("repurposing_plan"),
                        "quality_blocking": _gate_blocking(ctx, [f"plan-{row['opp_id']}",
                                                                 (script or {}).get("artifact_id", "")]),
                        **_biz(ctx)})
        saved = db.upsert(rec)
        ids[row["opp_id"]] = saved["id"]
    ctx.board["teaching_item_ids"] = ids


def _record(ctx) -> None:
    db = TeachingDB()
    item = ctx.board["teaching_item"]
    plan = (ctx.board.get("recording_plans") or [None])[0]
    script = (ctx.board.get("scripts") or [None])[0]
    blocking = _gate_blocking(ctx, [f"plan-{(plan or {}).get('opp_id')}", (script or {}).get("artifact_id", "")])
    if not plan or not script:
        blocking.append("recording plan or script missing (model backend unavailable?)")
    db.upsert({"id": item["id"], "recording_plan": plan, "script": script,
               "levels": ctx.board.get("teaching_levels"), "production": (ctx.board.get("production") or [None])[0],
               "estimated_recording_time": (plan or {}).get("estimated_recording_minutes"),
               "quality_blocking": blocking, "record_run_id": ctx.run_id})
    ctx.board["teaching_blocking"] = blocking
    status = db.get(item["id"])["status"]
    if not blocking and status == "SELECTED":
        try:
            status = db.transition(item["id"], "READY_TO_RECORD", "system", f"recording package {ctx.run_id}")["status"]
        except WorkflowError as exc:
            ctx.escalations.append(str(exc))
    ctx.board["teaching_status_after"] = status


def _content(ctx) -> None:
    db = TeachingDB()
    item = ctx.board["teaching_item"]
    plats = config.platforms()
    gate = ctx.board.get("quality_gate") or {}
    approvals = {}
    for a in ctx.board.get("content", []) or []:
        g = gate.get(a.get("artifact_id"), {})
        q = ctx.approvals.submit(
            category="publish_content", title=f"[{item['id']}] {a.get('format')}: {a.get('title', '')}"[:120],
            payload={"teaching_item": item["id"], "artifact_id": a.get("artifact_id"), "format": a.get("format"),
                     "platform": a.get("platform"), "text": a.get("text"), "value_statement": a.get("value_statement")},
            requested_by=a.get("produced_by", "?"), run_id=ctx.run_id,
            integration=plats.get(a.get("platform", ""), {}).get("integration"), blocked_reasons=g.get("blocking", []))
        approvals[a["artifact_id"]] = q["id"]
    t = ctx.board.get("transcript") or {}
    db.upsert({"id": item["id"], "content_formats": [
        {"format": a.get("format"), "platform": a.get("platform"), "artifact_id": a.get("artifact_id"),
         "approval_id": approvals.get(a.get("artifact_id")), "blocked": bool(gate.get(a.get("artifact_id"), {}).get("blocking"))}
        for a in ctx.board.get("content", []) or []],
        "transcript": {k: t.get(k) for k in ("source_file", "word_count", "duration_s", "format")},
        "content_run_id": ctx.run_id})
    ctx.board["teaching_approvals"] = approvals
