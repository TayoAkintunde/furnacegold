"""Security rules (Part 22)."""
from __future__ import annotations

import json
import re

from aibos import security
from aibos.paths import ROOT
from aibos.rules import artifacts, out, rule
from aibos.schemas import RunStatus, to_jsonable

# Phrases where an agent claims an external action already happened.
FAKE_ACTION = re.compile(r"\b(i|we) (have )?(published|posted|sent|emailed|deployed|launched|purchased|charged)\b|"
                         r"\b(has|have) been (published|posted|sent|deployed|launched)\b", re.I)


def _all_text(ctx) -> list[tuple[str, str]]:
    items = [(f"source:{s.source_id}", s.text) for s in ctx.sources.all()]
    items += [(f"claim:{c.claim_id}", c.text + " " + " ".join(c.quotes)) for c in ctx.claims]
    for k, v in ctx.board.items():
        if not k.startswith("_"):
            items.append((f"board:{k}", json.dumps(to_jsonable(v), default=str)))
    return items


def _findings_out(spec, ctx, findings, blocking: bool):
    data = [f.__dict__ for f in findings]
    if blocking and findings:
        ctx.escalations.append(f"{spec.agent_id}: {len(findings)} finding(s) — outputs blocked from leaving the system")
    return out(spec, ctx, status=RunStatus.OK,
               findings=[f"{len(findings)} finding(s)"] + [f"{f.kind}/{f.pattern} at {f.location}: {f.excerpt}" for f in findings[:20]],
               data={"security_findings": [dict(d, agent_id=spec.agent_id, blocking=blocking) for d in data]},
               confidence=1.0, next_action="remove/rotate the exposed value" if findings else "none")


@rule("secret_scan")
def secret_scan(ctx, spec):
    creds = spec.params.get("mode") == "credentials"
    found = []
    for loc, text in _all_text(ctx):
        if creds:
            found += [f for f in security.scan_secrets(text, loc) if f.pattern in security.CREDENTIAL_PATTERNS]
        else:
            found += [f for f in security.scan_secrets(text, loc, credentials=False)]
    return _findings_out(spec, ctx, found, blocking=True)


@rule("privacy")
def privacy(ctx, spec):
    found = []
    for a in artifacts(ctx):
        found += security.scan_pii(a["text"], f"artifact:{a['artifact_id']}")
    for k in ("knowledge", "audience_insights"):
        found += security.scan_pii(json.dumps(ctx.board.get(k, []), default=str), f"board:{k}")
    return _findings_out(spec, ctx, found, blocking=bool(found))


@rule("prompt_injection")
def prompt_injection(ctx, spec):
    found = []
    for s in ctx.sources.all():
        hits = security.scan_injection(s.text, f"source:{s.source_id}")
        if hits:
            found += hits
            if s.source_id not in ctx.quarantined_sources:
                ctx.quarantined_sources.append(s.source_id)
    res = _findings_out(spec, ctx, found, blocking=False)
    if ctx.quarantined_sources:
        res.recommendations.append(f"quarantined sources {ctx.quarantined_sources}: excluded from agent context; review manually")
    return res


@rule("external_action")
def external_action(ctx, spec):
    issues = []
    for o in ctx.outputs:
        blob = " ".join(map(str, o.findings + o.recommendations + [o.next_action]))
        if o.backend != "rule" and FAKE_ACTION.search(blob):
            issues.append(f"{o.agent_id} claims an external action happened; no integration performed it")
    for o in ctx.outputs:
        if o.data.get("executed_external_action"):
            issues.append(f"{o.agent_id} reported executing an external action directly")
    queued = {i["payload"].get("artifact_id") for i in ctx.approvals.list(None) if i.get("run_id") == ctx.run_id}
    unqueued = [a["artifact_id"] for a in artifacts(ctx) if a.get("platform") in ("x_post", "x_thread", "linkedin", "newsletter", "blog", "instagram", "tiktok", "youtube_shorts", "facebook", "reddit", "community", "seo_article", "podcast", "linkedin_carousel", "instagram_carousel") and a["artifact_id"] not in queued and not a.get("blocked")]
    if unqueued and "APPROVAL" in [s["stage"] for s in ctx.stage_log]:
        issues.append(f"publishable drafts not in approval queue: {unqueued}")
    if issues:
        ctx.escalations.extend(issues)
    return out(spec, ctx, findings=issues or ["no unapproved external actions; nothing was published"],
               data={"security_findings": [{"kind": "external_action", "excerpt": i, "agent_id": spec.agent_id,
                                            "blocking": True} for i in issues]}, confidence=1.0)


@rule("security_review")
def security_review(ctx, spec):
    findings = ctx.board.get("security_findings", []) or []
    blocking = [f for f in findings if f.get("blocking")]
    decision = "BLOCK" if blocking else "PASS"
    return out(spec, ctx, findings=[f"security decision: {decision}", f"{len(findings)} findings, {len(blocking)} blocking"],
               data={"security_decision": decision}, confidence=1.0)


@rule("permission_audit")
def permission_audit(ctx, spec):
    reg = ctx.registry
    issues = []
    if reg is None:
        return out(spec, ctx, status=RunStatus.SKIPPED, findings=["registry not attached to context"])
    risky = set(security.EXTERNAL_ACTION_CATEGORIES)
    for a in reg.all():
        both = set(a.allowed_actions) & set(a.restricted_actions)
        if both:
            issues.append(f"{a.agent_id}: actions both allowed and restricted {sorted(both)}")
        direct = set(a.allowed_actions) & risky
        if direct:
            issues.append(f"{a.agent_id}: allowed to perform external actions directly {sorted(direct)}")
    return out(spec, ctx, findings=[f"{len(issues)} permission issues across {len(reg)} agents"] + issues[:30],
               data={"permission_issues": issues}, confidence=1.0)


@rule("dependency_audit")
def dependency_audit(ctx, spec):
    issues, files = [], []
    for name in ("requirements.txt", "pyproject.toml"):
        p = ROOT / name
        if not p.exists():
            continue
        files.append(name)
        for line in p.read_text().splitlines():
            m = re.match(r'\s*"?([A-Za-z0-9_.\-\[\]]+)\s*([<>=!~]=?[^",]*)?"?,?\s*$', line)
            if name == "requirements.txt" and m and line.strip() and not line.strip().startswith("#"):
                if not m.group(2):
                    issues.append(f"{name}: {m.group(1)} is unpinned")
    return out(spec, ctx, findings=[f"audited {files or 'no dependency files'}; {len(issues)} issues"] + issues,
               data={"dependency_issues": issues}, confidence=0.8)


@rule("tool_risk")
def tool_risk(ctx, spec):
    reg = ctx.registry
    rows = {}
    if reg is not None:
        for a in reg.all():
            for t in a.tools:
                rows.setdefault(t, security.tool_risk(t))
    unknown = [t for t, r in rows.items() if r == "UNKNOWN"]
    return out(spec, ctx, findings=[f"{len(rows)} tools rated", f"unrated tools: {unknown}" if unknown else "all tools rated"],
               data={"tool_risk": rows}, confidence=1.0)
