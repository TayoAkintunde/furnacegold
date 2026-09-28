"""CLI commands for screen-recorded teaching: teach-today, record, content-from-recording, teaching."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aibos.evidence import SourceStore, claim_from_dict, source_from_dict
from aibos.teaching_db import TeachingDB, WorkflowError

GUIDING_QUESTION = ("What important thing happened in AI recently that I can demonstrate and teach people how to use?")


def _business_context() -> dict[str, Any]:
    from aibos import profile
    p = profile.load()
    rep = profile.check(p)
    if rep.status == "NOT_ANSWERED":
        return {"status": "NOT CONFIGURED — do not assume anything about the owner's audience, style or goals"}
    keep = ("target_audience", "content_platforms", "content_style", "topics_to_be_known_for", "topics_to_avoid",
            "expertise", "preferred_business_models", "available_time", "budget")
    return {"status": rep.status, **{k: p.get(k) for k in keep}}


def _opp_from_item(item: dict[str, Any]) -> dict[str, Any]:
    return {"opp_id": item["id"], "topic": item.get("topic"), "trend": item.get("trend"), "category": item.get("category"),
            "what_changed": item.get("what_changed"), "who_should_care": item.get("audience"),
            "problem_solved": item.get("problem_solved"), "teaching_angle": item.get("teaching_angle"),
            "demonstration": {"possible": True, "how": item.get("demo_idea")}, "difficulty": item.get("difficulty"),
            "value_answers": item.get("value_answers"), "claim_ids": [c["claim_id"] for c in item.get("claims") or []]}


def _seed(item: dict[str, Any]) -> tuple[SourceStore, list]:
    return (SourceStore(source_from_dict(s) for s in item.get("sources") or []),
            [claim_from_dict(c) for c in item.get("claims") or []])


def _orch(args):
    from aibos.backends import get_backend
    from aibos.orchestrator import MasterOrchestrator
    return MasterOrchestrator(backend=get_backend(args.backend, args.responses))


def _print(ctx, headline: str) -> None:
    print(headline)
    for s in ctx.stage_log:
        st = s.get("status") or ", ".join(f"{a.split('.')[-1]}={v}" for a, v in (s.get("statuses") or {}).items()) or "—"
        print(f"  {s['stage']:<22} {st}")
    for e in ctx.escalations:
        print(f"  ESCALATION: {e}")
    rp = next((o.data.get("report_path") for o in reversed(ctx.outputs) if o.agent_id == "teaching.reporter"), None)
    if rp:
        print(f"output: {rp}")


def cmd_teach_today(args):
    from aibos.cli import _sources
    focus = " ".join(getattr(args, "topic", []) or [])
    objective = f"TEACH TODAY{' (focus: ' + focus + ')' if focus else ''}: {GUIDING_QUESTION}"
    board = {"teaching_mode": "teach_today", "business_context": _business_context(),
             "teaching_learning": [TeachingDB().learning()] if not args.no_persist else []}
    ctx = _orch(args).run(objective, _sources(args), pipeline="teach_today", persist=not args.no_persist, board=board)
    sel = (ctx.board.get("teaching_selection") or [None])[0]
    if sel:
        iid = (ctx.board.get("teaching_item_ids") or {}).get(sel.get("opp_id"), "(not persisted)")
        head = f"TODAY'S SCREEN RECORDING: {sel.get('topic')}  [item {iid}, score {sel.get('score')}]"
    else:
        head = "TODAY'S SCREEN RECORDING: none — no topic passed the evidence / demonstration / value gates"
    _print(ctx, head)
    return 0


def _friendly(fn):
    """Unknown ids and workflow violations are user errors: print them, don't crash."""
    def wrapper(args):
        try:
            return fn(args)
        except (KeyError, WorkflowError) as exc:
            print(f"ERROR: {exc.args[0] if exc.args else exc}")
            return 1
    return wrapper


@_friendly
def cmd_record(args):
    db = TeachingDB()
    item = db.get(args.item_id)
    if item["status"] not in ("SELECTED", "READY_TO_RECORD"):
        print(f"{item['id']} is {item['status']}. /record needs a topic YOU approved: "
              f"`python -m aibos teaching select {item['id']} --by <you>`")
        return 1
    sources, claims = _seed(item)
    board: dict[str, Any] = {"teaching_mode": "record", "teaching_item": item, "teaching_selection": [_opp_from_item(item)]}
    if not args.regenerate:
        if item.get("recording_plan"):
            board["recording_plans"] = [item["recording_plan"]]
        if item.get("script"):
            board["scripts"] = [item["script"]]
    ctx = _orch(args).run(f"RECORD: complete screen-recording package for '{item.get('topic')}'", sources,
                          pipeline="record", persist=True, board=board, claims=claims)
    _print(ctx, f"RECORDING PACKAGE: {item.get('topic')}  -> status {ctx.board.get('teaching_status_after')}")
    return 0 if not ctx.board.get("teaching_blocking") else 2


@_friendly
def cmd_content_from_recording(args):
    db = TeachingDB()
    item = db.get(args.item_id)
    allowed = ("READY_TO_RECORD", "RECORDED", "EDITING", "READY_TO_PUBLISH")
    if item["status"] not in allowed:
        print(f"{item['id']} is {item['status']}; content-from-recording needs one of {allowed}")
        return 1
    path = Path(args.transcript)
    if not path.exists():
        print(f"transcript not found: {path}")
        return 1
    if item["status"] == "READY_TO_RECORD":
        item = db.transition(item["id"], "RECORDED", args.by, f"transcript supplied: {path.name}")
    sources, claims = _seed(item)
    board = {"teaching_mode": "content", "package_mode": "full", "teaching_item": item,
             "teaching_selection": [_opp_from_item(item)], "transcript_raw": path.read_text(),
             "transcript_path": str(path),
             "recording_plans": [item["recording_plan"]] if item.get("recording_plan") else [],
             "scripts": [item["script"]] if item.get("script") else []}
    ctx = _orch(args).run(f"CONTENT FROM RECORDING: repurpose the recording of '{item.get('topic')}'", sources,
                          pipeline="content_from_recording", persist=True, board=board, claims=claims)
    n = len(ctx.board.get("content") or [])
    blocked = sum(1 for a in ctx.board.get("content") or [] if a.get("blocked"))
    _print(ctx, f"CONTENT PACKAGE: {n} pieces ({blocked} blocked) queued for your approval — nothing published")
    return 0


def cmd_teaching(args):
    db = TeachingDB()
    try:
        if args.action == "list":
            items = db.all(args.status.upper() if args.status else None)
            if not items:
                print("no teaching items")
            for i in sorted(items, key=lambda x: (x.get("date_discovered") or "", x.get("score") or 0), reverse=True):
                rec = " *recommended*" if i.get("recommended") else ""
                print(f"{i['id']}  {i['status']:<16} {str(i.get('score', '')):<6} {i.get('date_discovered')}  "
                      f"{str(i.get('topic'))[:70]}{rec}")
        elif args.action == "show":
            print(json.dumps(db.get(args.item_id), indent=2, default=str))
        elif args.action == "select":
            i = db.transition(args.item_id, "SELECTED", args.by, args.note or "owner chose to record this")
            print(f"{i['id']} -> SELECTED. Next: python -m aibos record {i['id']}")
        elif args.action == "reject":
            i = db.transition(args.item_id, "REJECTED", args.by, args.note or "owner rejected")
            print(f"{i['id']} -> REJECTED")
        elif args.action == "advance":
            i = db.transition(args.item_id, args.to, args.by, args.note or "",
                              published_urls=args.url or None)
            print(f"{i['id']} -> {i['status']}")
        elif args.action == "analyze":
            from aibos.orchestrator import MasterOrchestrator
            from aibos.backends import get_backend
            ctx = MasterOrchestrator(backend=get_backend("offline")).run(
                "Teaching learning loop", pipeline="teaching_analytics",
                board={"teaching_mode": "learning", "teaching_item_id": args.item_id})
            _print(ctx, "TEACHING LEARNING LOOP")
    except (WorkflowError, KeyError) as exc:
        print(f"ERROR: {exc.args[0] if exc.args else exc}")
        return 1
    return 0


def add_parsers(sub, runopts) -> None:
    for name, help_ in (("teach-today", "TREND -> VERIFY -> TEACHING OPPORTUNITY -> RECORDING PLAN -> SCRIPT -> "
                                        "REPURPOSING -> BUSINESS -> APPROVAL QUEUE"),):
        p = runopts(sub.add_parser(name, help=help_))
        p.add_argument("topic", nargs="*", help="optional focus (e.g. 'coding agents')")
        p.set_defaults(func=cmd_teach_today)
    p = runopts(sub.add_parser("record", help="approved (SELECTED) topic -> complete screen-recording package"))
    p.add_argument("item_id")
    p.add_argument("--regenerate", action="store_true", help="re-create plan and script instead of reusing teach-today's")
    p.set_defaults(func=cmd_record)
    p = runopts(sub.add_parser("content-from-recording", help="recording transcript -> full repurposed content package"))
    p.add_argument("item_id")
    p.add_argument("--transcript", required=True, help=".txt, .srt or .vtt transcript of YOUR recording")
    p.add_argument("--by", default="owner", help="who recorded it (human workflow transition)")
    p.set_defaults(func=cmd_content_from_recording)
    p = sub.add_parser("teaching", help="teaching content database and workflow")
    p.add_argument("action", choices=["list", "show", "select", "reject", "advance", "analyze"])
    p.add_argument("item_id", nargs="?")
    p.add_argument("to", nargs="?", help="advance: target state (RECORDED, EDITING, READY_TO_PUBLISH, PUBLISHED)")
    p.add_argument("--status"); p.add_argument("--by", default="owner"); p.add_argument("--note")
    p.add_argument("--url", action="append", help="where you published it (required for PUBLISHED)")
    p.set_defaults(func=cmd_teaching)
