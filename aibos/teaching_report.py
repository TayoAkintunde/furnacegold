"""Markdown output for the teaching workflow: teach-today brief, recording package, content package."""
from __future__ import annotations

from typing import Any

from aibos.schemas import Verification

QUESTION = ("> **The question this system asks:** *What important thing happened in AI recently that I can "
            "demonstrate and teach people how to use?* — not *what AI news can I post today?*")


def _gate(ctx, aid: str) -> dict[str, Any]:
    return (ctx.board.get("quality_gate") or {}).get(aid, {})


def _checks(ctx, aid: str) -> list[str]:
    g = _gate(ctx, aid)
    if not g:
        return ["_not checked_"]
    lines = [f"- quality score {g.get('score')} — **{'BLOCKED' if g.get('blocking') else 'no blocking issues'}**"]
    lines += [f"- BLOCKING: {b}" for b in g.get("blocking", [])]
    lines += [f"- warning: {w}" for w in g.get("warnings", [])[:10]]
    return lines


def _plan_md(p: dict[str, Any]) -> list[str]:
    L = [f"**Hook ({(p.get('hook') or {}).get('seconds', '?')}s):** {(p.get('hook') or {}).get('text', '')}", "",
         f"**Context:** {p.get('context', '')}", "",
         f"**Audience:** {p.get('audience', '')}  ·  **Problem:** {p.get('problem', '')}  ·  "
         f"**Difficulty:** {p.get('difficulty', '')}  ·  **Estimated recording time:** {p.get('estimated_recording_minutes', '?')} min", "",
         "**Prerequisites:** " + "; ".join(p.get("prerequisites") or ["—"]), "",
         "| Step | On screen | Say | Why |", "|---|---|---|---|"]
    for s in p.get("demonstration") or []:
        L.append(f"| {s.get('step')} | {s.get('on_screen', '')} | {s.get('say', '')} | {s.get('why', '')} |".replace("\n", " "))
    L += ["", "**Teaching moments (pause and explain):**"]
    L += [f"- after step {t.get('at_step')}: {t.get('explain')}" for t in p.get("teaching_moments") or []]
    L += ["", f"**Proof (show the real result):** {p.get('proof', '')}", "",
          f"**Useful variation:** {p.get('variation', '')}", "",
          "**Limitations to say out loud:** " + "; ".join(p.get("limitations") or ["—"]), "",
          f"**Takeaway:** {p.get('takeaway', '')}", ""]
    if p.get("verify_before_recording"):
        L += ["**Verify on screen before recording:**"] + [f"- [ ] {v}" for v in p["verify_before_recording"]] + [""]
    return L


def _script_md(s: dict[str, Any]) -> list[str]:
    L = []
    for sec in s.get("sections") or []:
        L += [f"**[{sec.get('section', '').upper()}{' — step ' + str(sec['step']) if sec.get('step') else ''}]**", "",
              sec.get("text", ""), ""]
    return L or [s.get("text", ""), ""]


def _claims_md(ctx) -> list[str]:
    L = ["| Claim | Verification | Confidence | Sources |", "|---|---|---|---|"]
    for c in ctx.claims:
        L.append(f"| {c.claim_id}: {c.text} | {c.verification.value} | {c.confidence} | {', '.join(c.source_ids)} |")
    return L + [""]


def teach_today(ctx) -> str:
    b = ctx.board
    L = [f"# Teach Today — {ctx.today}", "", QUESTION, "",
         f"_Run `{ctx.run_id}` · backend: {ctx.backend_name} · nothing was recorded or published._", ""]
    L += ["## TODAY'S AI RADAR", ""]
    radar = b.get("radar") or []
    for r in radar:
        L.append(f"{r.get('rank', '-')}. **{r.get('development')}** ({r.get('category', '')}) — {r.get('why_teachable', '')} "
                 f"[claims: {', '.join(r.get('claim_ids', []))}]")
    if not radar:
        L += [f"- {f.get('development')}" for f in b.get("findings", []) or []] or ["_no developments (no sources / no model)_"]
    L += ["", "## TODAY'S TEACHING OPPORTUNITIES", "",
          "| Opp | Topic | Score | Value gate | Decision |", "|---|---|---|---|---|"]
    opps = {o.get("opp_id"): o for o in b.get("teaching_opportunities", []) or []}
    for r in b.get("teaching_scores", []) or []:
        o = opps.get(r["opp_id"], {})
        dec = "REJECTED: " + "; ".join(r["reasons"]) if r["rejected"] else "worth demonstrating"
        L.append(f"| {r['opp_id']} | {r['topic']} | {r['total']} | {o.get('value_gate', '?')} | {dec} |")
    L.append("")
    for r in b.get("teaching_scores", []) or []:
        bd = ", ".join(f"{k} {v:.2f}" for k, v in r["breakdown"].items())
        L += [f"- **{r['opp_id']}** breakdown: {bd}", f"  - notes: {'; '.join(n for n in r['notes'] if n)}"]
    L.append("")
    sel = (b.get("teaching_selection") or [None])[0]
    L += ["## TODAY'S SCREEN RECORDING", ""]
    if not sel:
        L += ["**No recommendation today.** No topic passed the evidence, demonstrability and value-first gates. "
              "Recording nothing is better than recording something weak.", ""]
    else:
        item_id = (b.get("teaching_item_ids") or {}).get(sel.get("opp_id"), "(not persisted)")
        plan = next((p for p in b.get("recording_plans", []) or [] if p.get("opp_id") == sel.get("opp_id")), {})
        script = next((s for s in b.get("scripts", []) or [] if s.get("opp_id") == sel.get("opp_id")), {})
        L += [f"### {plan.get('title') or sel.get('topic')}", "",
              f"- **Teaching item:** `{item_id}` (status RESEARCHED — you decide whether to record it)",
              f"- **Audience:** {plan.get('audience') or sel.get('who_should_care')}",
              f"- **Problem:** {plan.get('problem') or sel.get('problem_solved')}",
              f"- **What changed:** {sel.get('what_changed')}",
              f"- **Demo:** {sel.get('demonstration', {}).get('how')}",
              f"- **Value:** {', '.join(f'{k}: {v}' for k, v in (sel.get('value_answers') or {}).items() if v)}", ""]
        L += ["### Step-by-step recording plan", ""] + (_plan_md(plan) if plan else ["_no plan produced_", ""])
        L += ["**Plan checks:**"] + _checks(ctx, f"plan-{sel.get('opp_id')}") + [""]
        L += ["### Spoken script", ""] + (_script_md(script) if script else ["_no script produced_", ""])
        if script:
            L += ["**Script checks:**"] + _checks(ctx, script.get("artifact_id", "")) + [""]
        L += ["### Final takeaway", "", plan.get("takeaway") or "—", "",
              "### Repurposing plan", "", "| Format | Angle | Purpose | Audience |", "|---|---|---|---|"]
        for r in b.get("repurposing_plan", []) or []:
            L.append(f"| {r.get('format')} | {r.get('angle')} | {r.get('purpose')} | {r.get('audience')} |")
        L.append("")
        L += ["## TODAY'S BUSINESS OPPORTUNITY", ""]
        biz = b.get("teaching_business", []) or []
        genuine = [x for x in biz if x.get("genuine")]
        L += [f"- **{x['type']}** — {x.get('reasoning')} _Cheapest test:_ {x.get('cheapest_test', '—')}" for x in genuine] \
            or ["- None genuine for this topic. Not forcing it."]
        not_genuine = [x["type"] for x in biz if not x.get("genuine")]
        if not_genuine:
            L.append(f"- Not genuine here: {', '.join(not_genuine)}")
        L += ["", "## NEXT (your decision)", "",
              f"1. Review this brief. If you want to record it: `python -m aibos teaching select {item_id} --by <you>`",
              f"2. Build the full recording package: `python -m aibos record {item_id}`",
              f"3. After recording: `python -m aibos content-from-recording {item_id} --transcript <file>`", ""]
    L += ["## EVIDENCE", ""] + _claims_md(ctx)
    return "\n".join(L)


def recording(ctx) -> str:
    b = ctx.board
    item = b.get("teaching_item") or {}
    plan = (b.get("recording_plans") or [{}])[0]
    script = (b.get("scripts") or [{}])[0]
    prod = (b.get("production") or [{}])[0]
    L = [f"# Recording package — {plan.get('title') or item.get('topic')}", "",
         f"_Teaching item `{item.get('id')}` · status after this run: **{b.get('teaching_status_after', item.get('status'))}** · "
         f"run `{ctx.run_id}` · backend: {ctx.backend_name}_", "", QUESTION, ""]
    blocking = b.get("teaching_blocking") or []
    if blocking:
        L += ["> **NOT READY TO RECORD** — fix these first:"] + [f"> - {x}" for x in blocking] + [""]
    L += ["## 1. Before you press record", ""]
    for key, title in (("setup_checklist", "Setup"), ("accounts_and_costs", "Accounts and costs"), ("test_data", "Test data")):
        L += [f"**{title}:**"] + [f"- [ ] {x}" for x in prod.get(key) or ["—"]] + [""]
    L += ["## 2. Recording plan", ""] + _plan_md(plan) + ["**Plan checks:**"] + _checks(ctx, f"plan-{plan.get('opp_id')}") + [""]
    L += ["## 3. Spoken script", ""] + _script_md(script) + ["**Script checks:**"] + _checks(ctx, script.get("artifact_id", "")) + [""]
    L += ["## 4. Multi-level versions", ""]
    for lv in b.get("teaching_levels", []) or []:
        L += [f"### {str(lv.get('level', '')).title()}: {lv.get('title')}", f"- *Question:* {lv.get('question')}",
              f"- *Promise:* {lv.get('promise')}", f"- *Demo:* {lv.get('demo')}", f"- *Outcome:* {lv.get('outcome')}",
              f"- *Value:* {lv.get('value_statement')}", f"- *Length:* ~{lv.get('est_minutes')} min", ""]
    L += ["## 5. Production", "", "| Shot | On screen | Seconds |", "|---|---|---|"]
    L += [f"| {s.get('shot')} | {s.get('on_screen')} | {s.get('duration_s')} |" for s in prod.get("shot_list") or []]
    L += ["", "**On-screen callouts:**"] + [f"- {c}" for c in prod.get("callouts") or ["—"]]
    L += ["", "**Chapters:**"] + [f"- {c.get('time')} {c.get('title')}" for c in prod.get("chapters") or []]
    L += ["", "**Title options:**"] + [f"- {t}" for t in prod.get("title_options") or []]
    L += ["", "**Thumbnail text options:**"] + [f"- {t}" for t in prod.get("thumbnail_text_options") or []]
    L += ["", "**Description:**", "", prod.get("description", ""), "", "**Resources to link:**"]
    L += [f"- {r}" for r in prod.get("resources") or []]
    L += ["", "## 6. Evidence", ""] + _claims_md(ctx)
    L += ["## Next", "", "Record it yourself, then run:",
          f"`python -m aibos content-from-recording {item.get('id')} --transcript <transcript.srt|.vtt|.txt> --by <you>`", ""]
    return "\n".join(L)


def content(ctx) -> str:
    b = ctx.board
    item = b.get("teaching_item") or {}
    t = b.get("transcript") or {}
    L = [f"# Content package — {item.get('topic')}", "",
         f"_Teaching item `{item.get('id')}` · transcript {t.get('source_file')} ({t.get('word_count')} words, "
         f"{t.get('duration_s') or '?'}s) · run `{ctx.run_id}` · nothing was published._", ""]
    ta = (b.get("transcript_analysis") or [{}])[0]
    if ta:
        L += ["## What the recording actually showed", ""] + [f"- {x}" for x in ta.get("what_was_shown", [])] + [""]
        L += ["**Key moments:**"] + [f"- {m.get('time')} {m.get('description')}{' ✂ clip' if m.get('clip_candidate') else ''}"
                                     for m in ta.get("key_moments", [])] + [""]
        if ta.get("claims_made"):
            L += ["**Claims made on camera:**"] + [f"- {c.get('text')} — {c.get('claim_id') or 'NOT BACKED BY A VERIFIED CLAIM'}"
                                                   for c in ta["claims_made"]] + [""]
    pc = (b.get("package_checks") or [{}])[0]
    if pc:
        L += [f"**Formats present:** {', '.join(pc.get('formats_present', []))}",
              f"**Formats missing:** {', '.join(pc.get('formats_missing', [])) or 'none'}", ""]
    approvals = b.get("teaching_approvals") or {}
    for a in b.get("content", []) or []:
        g = _gate(ctx, a.get("artifact_id"))
        status = "BLOCKED" if g.get("blocking") else "PENDING YOUR APPROVAL"
        L += [f"## {a.get('format')} → {a.get('platform')}", "",
              f"- **Purpose:** {a.get('purpose', '')}  ·  **Audience:** {a.get('audience', '')}",
              f"- **Viewer can now:** {a.get('value_statement', '')}",
              f"- **Status:** {status}{' (approval ' + approvals[a['artifact_id']] + ')' if a.get('artifact_id') in approvals else ''}"]
        L += [f"- BLOCKING: {x}" for x in g.get("blocking", [])] + [f"- warning: {x}" for x in g.get("warnings", [])[:5]]
        L += ["", "```text", a.get("text", ""), "```", ""]
    L += ["## Next", "", "- Review drafts: `python -m aibos approvals list`",
          f"- When the video is edited: `python -m aibos teaching advance {item.get('id')} EDITING --by <you>`",
          f"- After YOU publish: `python -m aibos teaching advance {item.get('id')} READY_TO_PUBLISH --by <you>` then "
          f"`... PUBLISHED --url <url> --by <you>`",
          f"- After metrics exist: `python -m aibos teaching analyze {item.get('id')}`", ""]
    return "\n".join(L)


def learning(ctx) -> str:
    rows = ctx.board.get("teaching_learning") or []
    L = ["# Teaching learning loop", ""]
    for r in rows:
        for iid, p in (r.get("per_item") or {}).items():
            L += [f"## {iid}", ""] + [f"- {k}: {v}" for k, v in p.items()] + [""]
        lr = r.get("learning") or {}
        L += ["## What to teach next (viewer questions)", ""] + [f"- {q}" for q in lr.get("requested_topics", [])] + [""]
        L += ["## Category performance (feeds topic selection)", ""] + \
             [f"- {k}: {v}" for k, v in (lr.get("category_performance") or {}).items()] + [""]
    return "\n".join(L) if rows else "# Teaching learning loop\n\nNO DATA\n"


RENDERERS = {"teach_today": ("teach_today.md", teach_today), "record": ("recording_package.md", recording),
             "content": ("content_package.md", content), "learning": ("teaching_learning.md", learning)}


def render(ctx) -> tuple[str, str]:
    name, fn = RENDERERS[ctx.board.get("teaching_mode", "teach_today")]
    return name, fn(ctx)


def verified_claims_payload(ctx) -> list[dict[str, Any]]:
    from aibos.schemas import to_jsonable
    return [to_jsonable(c) for c in ctx.claims if c.verification == Verification.SUPPORTED]
