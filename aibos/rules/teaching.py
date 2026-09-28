"""Deterministic rules for screen-recorded teaching.

Scoring separates COMPUTED criteria (newness, evidence quality, audience interest from real data)
from JUDGED criteria (model judgements that must carry a justification or they score 0).
"""
from __future__ import annotations

import re
import statistics
from datetime import date
from itertools import combinations
from typing import Any

from aibos import analytics, config, paths
from aibos.evidence import normalize, parse_date
from aibos.rules import content_words, numbers_in, out, rule, words
from aibos.rules.content_quality import AI_SLOP, FINANCIAL_PROMISES, HYPE, MANIPULATIVE_CTA
from aibos.schemas import RunStatus, Verification

MONTHS = ("january|february|march|april|may|june|july|august|september|october|november|december|"
          "jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec")
DATE_RE = re.compile(rf"\b(?:{MONTHS})\.?\s+\d{{1,2}},\s+\d{{4}}\b|\b\d{{4}}-\d{{2}}-\d{{2}}\b", re.I)
MARKETING = ["revolutionary", "cutting-edge", "unlock", "supercharge", "seamless", "leverage", "synergy",
             "empower", "next-level", "world-class", "best-in-class", "transform your"]
MOTIVATIONAL = ["you've got this", "the future is now", "don't get left behind", "dream big", "hustle",
                "believe in yourself", "change your life"]
IDENT_RE = re.compile(r"`([^`]{2,80})`|\b([a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*[-_.]\d[a-z0-9]*(?:[-_.][a-z0-9]+)*)\b"
                      r"|\b([a-z_][a-z0-9_]{2,}\(\))", re.I)


def T() -> dict[str, Any]:
    return config.teaching()


def _db():
    from aibos.teaching_db import TeachingDB   # lazy: avoids an import cycle
    return TeachingDB()


def _issue(sev: str, msg: str) -> dict[str, str]:
    return {"severity": sev, "message": msg}


def _qrep(spec, artifact_id: str, score: float, issues: list[dict]) -> dict[str, Any]:
    return {"artifact_id": artifact_id, "agent_id": spec.agent_id, "score": round(max(0.0, min(1.0, score)), 3),
            "issues": issues}


def _qout(spec, ctx, reps: list[dict], extra: dict | None = None, **kw):
    blocking = sum(1 for r in reps for i in r["issues"] if i["severity"] == "BLOCKING")
    warns = sum(1 for r in reps for i in r["issues"] if i["severity"] == "WARN")
    return out(spec, ctx, findings=[f"{spec.name}: {len(reps)} item(s), {blocking} blocking, {warns} warnings"] +
               [f"{r['artifact_id']}: {i['severity']} {i['message']}" for r in reps for i in r["issues"]
                if i["severity"] != "INFO"][:12],
               data={"quality_reports": reps, **(extra or {})}, confidence=1.0 if reps else 0.0,
               uncertainties=[] if reps else ["nothing to check"], tests_performed=[spec.focus], **kw)


# ---------------------------------------------------------------- value first
def value_answer_ok(text: Any) -> tuple[bool, str]:
    cfg = T()
    t = str(text or "").strip()
    if len(words(t)) < int(cfg.get("min_value_answer_words", 6)):
        return False, "too short to be specific"
    low = t.lower()
    generic = [g for g in cfg.get("generic_value_phrases", []) if g in low]
    if generic and len(content_words(t)) < 8:
        return False, f"generic ({generic[0]!r})"
    return True, "specific"


@rule("teaching_value_gate")
def teaching_value_gate(ctx, spec):
    res, lines = {}, []
    for o in ctx.board.get("teaching_opportunities", []) or []:
        answers = o.get("value_answers") or {}
        ok = {k: value_answer_ok(v) for k, v in answers.items()}
        specific = [k for k, (good, _) in ok.items() if good]
        passed = bool(specific)
        o["value_gate"] = "PASS" if passed else "FAIL"
        res[o.get("opp_id")] = {"pass": passed, "specific_answers": specific,
                                "notes": {k: why for k, (good, why) in ok.items() if not good}}
        lines.append(f"{o.get('opp_id')} {o.get('topic', '')[:50]}: {'PASS' if passed else 'FAIL'} ({', '.join(specific) or 'no specific answer'})")
    return out(spec, ctx, findings=lines or ["no teaching opportunities"], data={"teaching_value": res}, confidence=1.0)


# ---------------------------------------------------------------- scoring
def _event_dates(ctx, claim_ids: list[str]) -> list[date]:
    today = date.fromisoformat(ctx.today)
    ds: list[date] = []
    for c in ctx.claims:
        if c.claim_id not in claim_ids or c.verification != Verification.SUPPORTED:
            continue
        ds += [d for m in DATE_RE.findall(c.text) if (d := parse_date(m) or _parse_long(m))]
        ds += [d for sid in c.source_ids if (s := ctx.sources.get(sid)) and (d := parse_date(s.published))]
    return [d for d in ds if d <= today]           # future dates (deprecations etc.) say nothing about newness


def _parse_long(s: str) -> date | None:
    from datetime import datetime
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%b. %d, %Y"):
        try:
            return datetime.strptime(s.replace("Sept ", "Sep "), fmt).date()
        except ValueError:
            continue
    return None


def _judged(o: dict, key: str) -> tuple[float, str]:
    j = (o.get("judgements") or {}).get(key) or {}
    score, why = j.get("score"), str(j.get("justification") or "")
    if not isinstance(score, (int, float)) or not 1 <= score <= 5:
        return 0.0, f"{key}: no valid 1-5 judgement"
    if len(words(why)) < 5:
        return 0.0, f"{key}: judgement without justification counts as 0"
    return (score - 1) / 4, ""


@rule("teaching_score")
def teaching_score(ctx, spec):
    cfg = T().get("scoring", {})
    w = cfg.get("weights", {})
    nd = cfg.get("newness_days", {"fresh": 7, "recent": 30, "aging": 90})
    today = date.fromisoformat(ctx.today)
    learning = _db().learning() if ctx.persist else {"category_performance": {}, "requested_topics": []}
    by_id = {c.claim_id: c for c in ctx.claims}
    rows = []
    for o in ctx.board.get("teaching_opportunities", []) or []:
        notes, reasons = [], []
        ids = o.get("claim_ids") or []
        verified = [by_id[i] for i in ids if i in by_id and by_id[i].verification == Verification.SUPPORTED]
        ev = (len(verified) / len(ids)) * statistics.fmean(c.confidence for c in verified) if verified else 0.0
        dates = _event_dates(ctx, ids)
        if dates:
            age = (today - max(dates)).days
            newness = 1.0 if age <= nd["fresh"] else 0.8 if age <= nd["recent"] else 0.5 if age <= nd["aging"] else 0.2
            notes.append(f"newest verified date {max(dates)} ({age} days)")
        else:
            newness = 0.5
            notes.append("newness: NO DATE in verified claims/sources (neutral 0.5)")
        s = {"newness": newness, "evidence_quality": round(ev, 3)}
        for k in ("practical_usefulness", "business_value"):
            s[k], n = _judged(o, k)
            notes += [n] if n else []
        j_edu, n = _judged(o, "educational_value")
        notes += [n] if n else []
        structure = (bool(o.get("beginner_mistakes")) + bool(o.get("simplest_example")) + bool(o.get("advanced_example"))) / 3
        s["educational_value"] = round(0.6 * j_edu + 0.4 * structure, 3)
        demo = o.get("demonstration") or {}
        j_demo, n = _judged(o, "demonstrability")
        notes += [n] if n else []
        s["demonstrability"] = j_demo if demo.get("possible") and str(demo.get("how", "")).strip() else 0.0
        j_res, n = _judged(o, "meaningful_result")
        notes += [n] if n else []
        s["meaningful_result"] = j_res if str(o.get("what_to_build", "")).strip() else 0.0
        cat = (learning.get("category_performance") or {}).get(o.get("category", ""))
        requested = [t for t in learning.get("requested_topics", []) if _sim(t, o.get("topic", "")) >= 0.3]
        if cat is not None:
            s["audience_interest"] = round(min(1.0, float(cat) + (0.1 if requested else 0)), 3)
            notes.append(f"audience interest from past performance of '{o.get('category')}'")
        elif requested:
            s["audience_interest"] = 0.7
            notes.append(f"viewers asked for this before: {requested[:2]}")
        else:
            s["audience_interest"] = 0.5
            notes.append("audience interest: NO DATA yet (neutral 0.5) — improves once published videos are analysed")
        total = round(sum(w.get(k, 0) * v for k, v in s.items()), 3)
        # hard gates
        if o.get("value_gate") == "FAIL":
            reasons.append("value-first: cannot say specifically what the viewer can now do")
        if len(verified) < int(cfg.get("min_verified_claims", 1)):
            reasons.append("no verified claims behind this topic")
        if ev < float(cfg.get("min_evidence_quality", 0.5)):
            reasons.append(f"evidence quality {ev:.2f} below {cfg.get('min_evidence_quality', 0.5)}")
        if s["demonstrability"] < float(cfg.get("min_demonstrability", 0.4)):
            reasons.append("cannot be demonstrated on screen with a meaningful result")
        if o.get("reject_reason"):
            reasons.append(f"analyst: {o['reject_reason']}")
        if ctx.persist:
            # "already covered" = the owner already selected/recorded it; merely-researched topics may resurface
            dupes = [d for d in _db().find_similar(o.get("topic", "")) if d["status"] not in ("REJECTED", "RESEARCHED")]
            if dupes:
                reasons.append(f"already covered: {dupes[0]['id']} ({dupes[0]['status']})")
        if total < float(cfg.get("min_total_score", 0.55)):
            reasons.append(f"total score {total} below {cfg.get('min_total_score')}")
        rows.append({"opp_id": o.get("opp_id"), "topic": o.get("topic"), "category": o.get("category"),
                     "total": total, "breakdown": s, "notes": notes, "rejected": bool(reasons), "reasons": reasons})
    rows.sort(key=lambda r: (r["rejected"], -r["total"]))
    best = next((r for r in rows if not r["rejected"]), None)
    selection = []
    if best:
        opp = next(o for o in ctx.board["teaching_opportunities"] if o.get("opp_id") == best["opp_id"])
        selection = [dict(opp, score=best["total"], score_breakdown=best["breakdown"])]
    elif rows:
        ctx.escalations.append("TEACH: no topic passed today's bar — recording nothing beats recording something weak")
    return out(spec, ctx,
               findings=[f"{r['opp_id']} {str(r['topic'])[:60]}: {r['total']} "
                         f"{'REJECTED: ' + '; '.join(r['reasons']) if r['rejected'] else 'OK'}" for r in rows]
               or ["no teaching opportunities to score"],
               data={"teaching_scores": rows, "teaching_selection": selection},
               next_action=f"recommend {best['opp_id']} for recording" if best else "capture better sources / try again tomorrow",
               confidence=1.0)


def _sim(a: str, b: str) -> float:
    wa, wb = content_words(a), content_words(b)
    return len(wa & wb) / len(wa | wb) if wa and wb else 0.0


# ---------------------------------------------------------------- recording checks
def _spoken_seconds(text: str) -> float:
    return len(words(text)) / (float(T().get("recording", {}).get("words_per_minute", 150)) / 60)


@rule("recording_feasibility")
def recording_feasibility(ctx, spec):
    rc = T().get("recording", {})
    lo, hi = rc.get("hook_seconds", [5, 15])
    reps = []
    for p in ctx.board.get("recording_plans", []) or []:
        aid = f"plan-{p.get('opp_id')}"
        issues = []
        for sec in rc.get("required_plan_sections", []):
            if not p.get(sec):
                issues.append(_issue("BLOCKING", f"plan section missing: {sec}"))
        steps = p.get("demonstration") or []
        if len(steps) < int(rc.get("demo_min_steps", 4)):
            issues.append(_issue("BLOCKING", f"only {len(steps)} demonstration steps (need {rc.get('demo_min_steps', 4)})"))
        vague = [s.get("step") for s in steps if len(words(s.get("on_screen", ""))) < 3]
        if vague:
            issues.append(_issue("WARN", f"steps {vague} do not say what is on screen"))
        hook = (p.get("hook") or {}).get("text", "")
        secs = _spoken_seconds(hook)
        if hook and not lo <= secs <= hi:
            issues.append(_issue("WARN", f"hook takes ~{secs:.0f}s to say (target {lo}-{hi}s)"))
        if p.get("proof") and len(words(p["proof"])) < 5:
            issues.append(_issue("WARN", "proof is vague; show the actual result"))
        if not p.get("prerequisites"):
            issues.append(_issue("WARN", "no prerequisites/accounts listed"))
        if not p.get("limitations"):
            issues.append(_issue("WARN", "no limitations stated"))
        for v in p.get("verify_before_recording") or []:
            issues.append(_issue("INFO", f"verify before recording: {v}"))
        reps.append(_qrep(spec, aid, 1 - 0.5 * any(i["severity"] == "BLOCKING" for i in issues)
                          - 0.05 * sum(i["severity"] == "WARN" for i in issues), issues))
    return _qout(spec, ctx, reps)


@rule("script_quality")
def script_quality(ctx, spec):
    rc = T().get("recording", {})
    lo, hi = rc.get("hook_seconds", [5, 15])
    plans = {p.get("opp_id"): p for p in ctx.board.get("recording_plans", []) or []}
    reps = []
    for s in ctx.board.get("scripts", []) or []:
        issues = []
        text = s.get("text") or " ".join(x.get("text", "") for x in s.get("sections", []))
        low = text.lower()
        kinds = {x.get("section") for x in s.get("sections", [])}
        need = {"hook": "hook", "takeaway": "takeaway", "caveat": "caveat", "correction": "mistake"}
        for req in rc.get("required_script_elements", []):
            if need.get(req, req) not in kinds:
                issues.append(_issue("WARN", f"script has no '{need.get(req, req)}' section"))
        hook = next((x.get("text", "") for x in s.get("sections", []) if x.get("section") == "hook"), "")
        if hook and not lo <= _spoken_seconds(hook) <= hi:
            issues.append(_issue("WARN", f"spoken hook ~{_spoken_seconds(hook):.0f}s (target {lo}-{hi}s)"))
        urgency = [p for p in MANIPULATIVE_CTA if re.search(p, low)]
        money = [p for p in FINANCIAL_PROMISES if re.search(p, low)]
        if urgency or money:
            issues.append(_issue("BLOCKING", f"fake urgency / promises: {urgency + money}"))
        for label, lst in (("hype", HYPE), ("marketing tone", MARKETING), ("motivational filler", MOTIVATIONAL),
                           ("AI filler", AI_SLOP)):
            hits = [p for p in lst if p in low]
            if hits:
                issues.append(_issue("WARN", f"{label}: {hits}"))
        if low.count(" you") < 3:
            issues.append(_issue("WARN", "rarely addresses the viewer; teaching should talk to 'you'"))
        minutes = _spoken_seconds(text) / 60
        plan_min = (plans.get(s.get("opp_id")) or {}).get("estimated_recording_minutes")
        issues.append(_issue("INFO", f"~{minutes:.1f} min of speech ({len(words(text))} words)"))
        if isinstance(plan_min, (int, float)) and minutes > plan_min * 1.5:
            issues.append(_issue("WARN", f"script needs ~{minutes:.0f} min but the plan allows {plan_min}"))
        blocking = any(i["severity"] == "BLOCKING" for i in issues)
        reps.append(_qrep(spec, s.get("artifact_id", "script"), 0 if blocking else
                          1 - 0.08 * sum(i["severity"] == "WARN" for i in issues), issues))
    return _qout(spec, ctx, reps)


@rule("technical_identifiers")
def technical_identifiers(ctx, spec):
    verified_text = " ".join(c.text for c in ctx.claims if c.verification == Verification.SUPPORTED)
    source_text = " ".join(s.text for s in ctx.sources.all() if s.source_id not in ctx.quarantined_sources)
    haystack = normalize(verified_text + " " + source_text + " " + (ctx.board.get("transcript") or {}).get("text", ""))
    reps = []
    items = [(f"plan-{p.get('opp_id')}", " ".join([str(p.get("hook", "")), str(p.get("context", ""))] +
             [f"{x.get('on_screen', '')} {x.get('say', '')}" for x in p.get("demonstration", []) or []]))
             for p in ctx.board.get("recording_plans", []) or []]
    items += [(s.get("artifact_id", "script"), s.get("text", "")) for s in ctx.board.get("scripts", []) or []]
    for aid, text in items:
        idents = sorted({(a or b or c).strip() for a, b, c in IDENT_RE.findall(text)})
        idents = [i for i in idents if not re.fullmatch(r"[\d.:,-]+", i)]
        missing = [i for i in idents if normalize(i).rstrip("()") not in haystack]
        issues = [_issue("INFO", f"{len(idents) - len(missing)}/{len(idents)} technical identifiers found in verified sources")]
        if missing:
            issues.append(_issue("WARN", f"not found in verified sources — check on screen before recording: {missing[:8]}"))
        reps.append(_qrep(spec, aid, 1 - 0.5 * (len(missing) / len(idents)) if idents else 1.0, issues))
    return _qout(spec, ctx, reps)


# ---------------------------------------------------------------- package checks
def _grams(text: str, n: int = 6) -> set:
    ws = words(text)
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


@rule("repurpose_quality")
def repurpose_quality(ctx, spec):
    cfg = T()
    wanted = list((cfg.get("package_formats") or {}).keys())
    pkg = [a for a in ctx.board.get("content", []) or [] if a.get("format")]
    have = {a.get("format") for a in pkg}
    reps = []
    missing = [f for f in wanted if f not in have]
    if ctx.board.get("package_mode") == "full" and missing:
        reps.append(_qrep(spec, "package", 1 - len(missing) / len(wanted),
                          [_issue("WARN", f"formats missing from the package: {missing}")]))
    limit = float(cfg.get("max_cross_format_overlap", 0.35))
    grams = {a["artifact_id"]: _grams(a.get("text", "")) for a in pkg}
    dup: dict[str, list[str]] = {}
    for a, b in combinations(pkg, 2):
        ga, gb = grams[a["artifact_id"]], grams[b["artifact_id"]]
        if ga and gb:
            ov = len(ga & gb) / min(len(ga), len(gb))
            if ov > limit:
                dup.setdefault(a["artifact_id"], []).append(f"{b['artifact_id']} ({ov:.0%})")
    for a in pkg:
        issues = []
        if dup.get(a["artifact_id"]):
            issues.append(_issue("WARN", f"duplicates rather than adapts: overlaps {dup[a['artifact_id']]}"))
        if a.get("platform") != (cfg.get("package_formats") or {}).get(a.get("format")):
            issues.append(_issue("WARN", f"format {a.get('format')} should use platform "
                                         f"{(cfg.get('package_formats') or {}).get(a.get('format'))}"))
        if not a.get("purpose"):
            issues.append(_issue("INFO", "no stated purpose"))
        reps.append(_qrep(spec, a["artifact_id"], 1 - 0.3 * bool(dup.get(a["artifact_id"])), issues))
    return _qout(spec, ctx, reps, extra={"package_checks": [{"formats_present": sorted(have), "formats_missing": missing}]})


# ---------------------------------------------------------------- transcript
TS_RE = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?")


def _secs(m) -> float:
    h, mnt, s, ms = m.groups()
    return int(h or 0) * 3600 + int(mnt) * 60 + int(s) + int((ms or "0").ljust(3, "0")) / 1000


def parse_transcript(raw: str) -> dict[str, Any]:
    lines = [l.rstrip() for l in raw.splitlines()]
    segments, cur = [], None
    fmt = "srt/vtt" if any("-->" in l for l in lines) else "plain"
    for line in lines:
        if "-->" in line:
            times = list(TS_RE.finditer(line))
            if len(times) >= 2:
                cur = {"start": _secs(times[0]), "end": _secs(times[1]), "text": ""}
                segments.append(cur)
            continue
        if fmt == "srt/vtt":
            if line.strip().isdigit() or line.strip() in ("", "WEBVTT"):
                continue
            if cur is not None:
                cur["text"] = (cur["text"] + " " + line.strip()).strip()
        else:
            m = re.match(r"^\[?((?:\d+:)?\d{1,2}:\d{2})\]?\s+(.*)$", line.strip())
            if m:
                t = TS_RE.match(m.group(1))
                segments.append({"start": _secs(t), "end": None, "text": m.group(2)})
            elif line.strip():
                segments.append({"start": None, "end": None, "text": line.strip()})
    text = " ".join(s["text"] for s in segments)
    starts = [s["start"] for s in segments if s["start"] is not None]
    ends = [s["end"] for s in segments if s.get("end") is not None]
    duration = max(ends or starts or [0]) if (ends or starts) else None
    wc = len(words(text))
    return {"format": fmt, "segments": segments, "text": text, "word_count": wc,
            "duration_s": duration, "words_per_minute": round(wc / (duration / 60), 1) if duration else None}


@rule("transcript_ingest")
def transcript_ingest(ctx, spec):
    raw = ctx.board.get("transcript_raw")
    if not raw:
        return out(spec, ctx, status=RunStatus.DEGRADED, findings=["NO TRANSCRIPT supplied; nothing to repurpose"],
                   next_action="aibos content-from-recording <id> --transcript FILE")
    t = parse_transcript(raw)
    t["source_file"] = ctx.board.get("transcript_path")
    return out(spec, ctx, findings=[f"{t['format']} transcript: {len(t['segments'])} segments, {t['word_count']} words, "
                                    f"duration {t['duration_s'] or 'unknown'}s"],
               data={"transcript": t}, confidence=1.0)


# ---------------------------------------------------------------- learning loop
@rule("teaching_performance")
def teaching_performance(ctx, spec):
    cfg = T()
    db = _db()
    prefix = cfg.get("retention_curve_prefix", "retention_at_")
    rows = analytics.load_metrics()
    target = ctx.board.get("teaching_item_id")
    items = [i for i in db.all() if i["status"] in ("PUBLISHED", "ANALYZED") and (not target or i["id"] == target)]
    if not items:
        return out(spec, ctx, status=RunStatus.DEGRADED,
                   findings=["NO DATA: no PUBLISHED teaching items to analyse"],
                   next_action="after you publish: aibos teaching advance <id> PUBLISHED --url <url>, then export metrics")
    fb_dir = paths.sub("feedback")
    per_item, findings = {}, []
    for it in items:
        mine = [r for r in rows if r.asset_id == it["id"]]
        totals: dict[str, float] = {}
        curve = []
        for r in mine:
            if r.metric.startswith(prefix):
                m = re.match(rf"{re.escape(prefix)}(\d+)s?", r.metric)
                if m:
                    curve.append((int(m.group(1)), r.value))
            else:
                totals[r.metric] = totals.get(r.metric, 0) + r.value
        curve.sort()
        drop = None
        if len(curve) >= 2:
            drops = [(a[0], b[0], a[1] - b[1]) for a, b in zip(curve, curve[1:])]
            drop = max(drops, key=lambda d: d[2])
        questions = []
        for f in sorted(fb_dir.glob(f"{it['id']}*")):
            questions += [l.strip() for l in f.read_text().splitlines() if l.strip().endswith("?")]
        clusters: list[list[str]] = []
        for q in questions:
            for c in clusters:
                if _sim(q, c[0]) >= 0.5:
                    c.append(q)
                    break
            else:
                clusters.append([q])
        repeated = [c[0] for c in clusters if len(c) >= 2]
        if not mine and not questions:
            per_item[it["id"]] = {"status": "NO DATA"}
            findings.append(f"{it['id']}: NO DATA (export metrics with asset_id={it['id']})")
            continue
        perf = {"metrics": totals, "retention_curve": curve,
                "biggest_dropoff": {"from_s": drop[0], "to_s": drop[1], "lost": round(drop[2], 3)} if drop else None,
                "questions": len(questions), "repeated_questions": repeated}
        per_item[it["id"]] = perf
        findings.append(f"{it['id']}: views={totals.get('views', 'n/a')} retention={totals.get('retention_rate', 'n/a')} "
                        f"dropoff={perf['biggest_dropoff']} repeated questions={len(repeated)}")
    # relative performance by category (needs >=2 analysed items to compare)
    learning = db.learning()
    scored = [(it, per_item[it["id"]]) for it in items if per_item.get(it["id"], {}).get("metrics", {}).get("views")]
    if len(scored) >= 2:
        med = statistics.median(p["metrics"]["views"] for _, p in scored)
        cats: dict[str, list[float]] = {}
        for it, p in scored:
            rel = min(1.0, 0.5 * p["metrics"]["views"] / med) if med else 0.5
            cats.setdefault(it.get("category") or "uncategorised", []).append(rel)
        learning["category_performance"] = {k: round(statistics.fmean(v), 3) for k, v in cats.items()}
    else:
        findings.append("category comparison needs at least 2 analysed videos with views")
    req = set(learning.get("requested_topics", []))
    for p in per_item.values():
        req |= set(p.get("repeated_questions", []))
    learning["requested_topics"] = sorted(req)
    hooks = learning.get("hook_findings", [])
    for it, p in scored:
        r15 = next((v for s, v in p.get("retention_curve", []) if s <= 15), None)
        if r15 is not None:
            hooks.append({"item": it["id"], "hook": (it.get("recording_plan") or {}).get("hook", {}).get("text"),
                          "retention_at_15s": r15})
    learning["hook_findings"] = hooks[-50:]
    if ctx.persist:
        db.save_learning(learning)
        for it in items:
            p = per_item.get(it["id"])
            if p and p.get("status") != "NO DATA":
                lessons = []
                if p.get("biggest_dropoff"):
                    d = p["biggest_dropoff"]
                    lessons.append(f"biggest drop-off between {d['from_s']}s and {d['to_s']}s — review that part of the recording")
                if p.get("repeated_questions"):
                    lessons.append(f"viewers repeatedly asked: {p['repeated_questions'][:3]} — candidate next lessons")
                db.upsert({"id": it["id"], "performance": p, "lessons_learned": lessons})
                if it["status"] == "PUBLISHED":
                    db.transition(it["id"], "ANALYZED", "system", "learning loop analysed supplied metrics")
    return out(spec, ctx, findings=findings, data={"teaching_learning": [{"per_item": per_item, "learning": learning}]},
               confidence=0.8)


# ---------------------------------------------------------------- report
@rule("teaching_report")
def teaching_report(ctx, spec):
    from aibos.teaching_report import render
    name, md = render(ctx)
    path = ctx.run_dir / name
    path.write_text(md)
    files = [str(path)]
    item = ctx.board.get("teaching_item") or {}
    if item.get("id") and ctx.persist:                      # keep the package next to the teaching item too
        item_path = paths.sub("teaching") / item["id"] / name
        item_path.parent.mkdir(parents=True, exist_ok=True)
        item_path.write_text(md)
        files.append(str(item_path))
    return out(spec, ctx, findings=[f"{name} written ({len(md)} chars)"], data={"report_path": str(path)},
               files_changed=files, confidence=1.0)
