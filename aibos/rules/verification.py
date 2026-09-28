"""Verification rules (Part 5). Each returns per-claim verdicts: pass | fail | warn | na."""
from __future__ import annotations

from datetime import date
from itertools import combinations

from aibos.evidence import PRIMARY_TYPES, SOURCE_TIER, normalize, parse_date, quote_in_text
from aibos.rules import content_words, numbers_in, out, rule


def _report(spec, ctx, results: dict, extra_findings: list | None = None, data: dict | None = None):
    counts: dict[str, int] = {}
    for r in results.values():
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    findings = [f"{spec.name}: {counts}"] + (extra_findings or [])
    fails = [f"{cid}: {r['note']}" for cid, r in results.items() if r["verdict"] == "fail"]
    return out(spec, ctx, findings=findings, uncertainties=fails,
               data={"verification_reports": [{"agent_id": spec.agent_id, "results": results}], **(data or {})},
               tests_performed=[spec.focus], confidence=1.0,
               next_action="aggregate verdicts" if not fails else "send failed claims back to research or drop them")


def _cited(ctx, claim):
    return [s for sid in claim.source_ids if (s := ctx.sources.get(sid)) and sid not in ctx.quarantined_sources]


@rule("citation")
def citation(ctx, spec):
    res = {}
    for c in ctx.claims:
        if not c.source_ids:
            res[c.claim_id] = {"verdict": "fail", "note": "no source cited"}
            continue
        missing = [sid for sid in c.source_ids if not ctx.sources.get(sid)]
        quarantined = [sid for sid in c.source_ids if sid in ctx.quarantined_sources]
        if missing:
            res[c.claim_id] = {"verdict": "fail", "note": f"cites unknown source(s) {missing}"}
        elif quarantined and len(quarantined) == len(c.source_ids):
            res[c.claim_id] = {"verdict": "fail", "note": f"only cites quarantined source(s) {quarantined}"}
        else:
            res[c.claim_id] = {"verdict": "pass", "note": f"cites {c.source_ids}"}
    return _report(spec, ctx, res)


@rule("primary_source")
def primary_source(ctx, spec):
    res = {}
    for c in ctx.claims:
        cited = _cited(ctx, c)
        if not cited:
            res[c.claim_id] = {"verdict": "fail", "note": "no usable cited source"}
            continue
        if not c.quotes:
            res[c.claim_id] = {"verdict": "fail", "note": "no verbatim evidence quote supplied"}
            continue
        located = {}
        for q in c.quotes:
            hit = next((s for s in cited if quote_in_text(q, s.text)), None)
            located[q] = hit
        missing = [q[:60] for q, s in located.items() if s is None]
        if missing:
            res[c.claim_id] = {"verdict": "fail", "note": f"quote not found verbatim in cited sources: {missing}"}
            continue
        primary = [s for s in located.values() if s.source_type in PRIMARY_TYPES]
        if primary:
            res[c.claim_id] = {"verdict": "pass", "note": f"quote found in primary source {primary[0].source_id} ({primary[0].publisher})"}
        else:
            res[c.claim_id] = {"verdict": "warn", "note": "quote found, but only in secondary sources"}
    return _report(spec, ctx, res)


@rule("quote")
def quote(ctx, spec):
    import re
    res = {}
    for c in ctx.claims:
        inner = re.findall(r'"([^"]{8,})"|“([^”]{8,})”', c.text)
        inner = [a or b for a, b in inner]
        cited = _cited(ctx, c)
        checks = inner + list(c.quotes)
        if not checks:
            res[c.claim_id] = {"verdict": "na", "note": "no quotations"}
            continue
        bad = [q[:60] for q in checks if not any(quote_in_text(q, s.text) for s in cited)]
        res[c.claim_id] = ({"verdict": "fail", "note": f"not verbatim in any cited source: {bad}"} if bad
                           else {"verdict": "pass", "note": f"{len(checks)} quotation(s) verbatim"})
    return _report(spec, ctx, res)


@rule("statistics")
def statistics_(ctx, spec):
    res = {}
    for c in ctx.claims:
        nums = numbers_in(c.text)
        if not nums:
            res[c.claim_id] = {"verdict": "na", "note": "no numbers"}
            continue
        blob = " ".join(normalize(s.text).replace(",", "") for s in _cited(ctx, c))
        src_nums = set(numbers_in(blob))
        missing = [n for n in nums if n not in src_nums]
        res[c.claim_id] = ({"verdict": "fail", "note": f"numbers not in cited sources: {missing}"} if missing
                           else {"verdict": "pass", "note": f"numbers {nums} found in sources"})
    return _report(spec, ctx, res)


@rule("date")
def date_check(ctx, spec):
    window = int(spec.params.get("max_age_days", 120))
    today = date.fromisoformat(ctx.today)
    res = {}
    for c in ctx.claims:
        dates = [parse_date(s.published) for s in _cited(ctx, c)]
        dates = [d for d in dates if d]
        if not dates:
            res[c.claim_id] = {"verdict": "warn", "note": "no parseable publication date on cited sources"}
            continue
        newest = max(dates)
        age = (today - newest).days
        if age < 0:
            res[c.claim_id] = {"verdict": "warn", "note": f"source date {newest} is in the future — check it"}
        elif age > window:
            res[c.claim_id] = {"verdict": "warn", "note": f"newest source is {age} days old (> {window})"}
        else:
            res[c.claim_id] = {"verdict": "pass", "note": f"newest source {newest} ({age} days old)"}
    return _report(spec, ctx, res)


@rule("claim_support")
def claim_support(ctx, spec):
    res = {}
    for c in ctx.claims:
        cw = content_words(c.text)
        qw = content_words(" ".join(c.quotes))
        if not cw or not qw:
            res[c.claim_id] = {"verdict": "fail", "note": "no quoted evidence to compare"}
            continue
        overlap = len(cw & qw) / len(cw)
        verdict = "pass" if overlap >= 0.5 else "warn" if overlap >= 0.25 else "fail"
        res[c.claim_id] = {"verdict": verdict, "note": f"claim/evidence term overlap {overlap:.0%}"}
    return _report(spec, ctx, res)


@rule("cross_source")
def cross_source(ctx, spec):
    need = int(spec.params.get("min_publishers", 2))
    res = {}
    for c in ctx.claims:
        cited = _cited(ctx, c)
        supporting = {s.publisher for s in cited
                      if not c.quotes or any(quote_in_text(q, s.text) for q in c.quotes)}
        if len(supporting) >= need:
            res[c.claim_id] = {"verdict": "pass", "note": f"{len(supporting)} independent publishers: {sorted(supporting)}"}
        else:
            res[c.claim_id] = {"verdict": "warn", "note": f"only {len(supporting)} publisher(s) {sorted(supporting)}; independent corroboration absent"}
    return _report(spec, ctx, res)


@rule("contradiction")
def contradiction(ctx, spec):
    """Same statement, different numbers. Prefer the claim whose numbers appear in its
    own cited source text (primary evidence); fail both only if neither/both are supported."""
    res = {c.claim_id: {"verdict": "pass", "note": "no contradiction detected"} for c in ctx.claims}
    found = []

    def supported(c) -> bool:
        blob = " ".join(normalize(s.text).replace(",", "") for s in _cited(ctx, c))
        src = set(numbers_in(blob))
        return bool(src) and all(n in src for n in numbers_in(c.text))

    for a, b in combinations(ctx.claims, 2):
        wa, wb = content_words(a.text), content_words(b.text)
        if not wa or not wb:
            continue
        sim = len(wa & wb) / len(wa | wb)
        na, nb = set(numbers_in(a.text)), set(numbers_in(b.text))
        if sim >= 0.6 and na and nb and na != nb:
            note = f"{a.claim_id} and {b.claim_id} state different numbers ({sorted(na)} vs {sorted(nb)})"
            sa, sb = supported(a), supported(b)
            if sa and not sb:
                res[b.claim_id] = {"verdict": "fail", "note": note + f"; source text supports {a.claim_id}"}
                resolution = f"{a.claim_id} kept (its numbers appear in its sources); {b.claim_id} rejected"
            elif sb and not sa:
                res[a.claim_id] = {"verdict": "fail", "note": note + f"; source text supports {b.claim_id}"}
                resolution = f"{b.claim_id} kept (its numbers appear in its sources); {a.claim_id} rejected"
            else:
                res[a.claim_id] = res[b.claim_id] = {"verdict": "fail", "note": note + "; unresolved"}
                resolution = "unresolved — both rejected pending primary-source check"
            found.append({"claims": [a.claim_id, b.claim_id], "note": note, "resolution": resolution})
    return _report(spec, ctx, res, data={"contradictions": found})


@rule("outdated")
def outdated(ctx, spec):
    stale = int(spec.params.get("stale_days", 365))
    today = date.fromisoformat(ctx.today)
    res = {}
    for c in ctx.claims:
        ds = [d for s in _cited(ctx, c) if (d := parse_date(s.published))]
        if not ds:
            res[c.claim_id] = {"verdict": "na", "note": "no dates"}
        elif (today - max(ds)).days > stale:
            res[c.claim_id] = {"verdict": "warn", "note": f"newest evidence older than {stale} days"}
        else:
            res[c.claim_id] = {"verdict": "pass", "note": "evidence is current"}
    return _report(spec, ctx, res)


@rule("source_quality")
def source_quality(ctx, spec):
    scores = {s.source_id: {"type": s.source_type, "publisher": s.publisher,
                            "score": SOURCE_TIER.get(s.source_type, 0.2),
                            "has_date": bool(parse_date(s.published)), "has_text": len(s.text) > 200}
              for s in ctx.sources.all()}
    res = {}
    for c in ctx.claims:
        best = max((scores[sid]["score"] for sid in c.source_ids if sid in scores), default=0.0)
        verdict = "pass" if best >= 0.6 else "warn" if best >= 0.4 else "fail"
        res[c.claim_id] = {"verdict": verdict, "note": f"best source score {best:.2f}"}
    weak = [f"{sid}: {v['type']} ({v['score']})" for sid, v in scores.items() if v["score"] < 0.5]
    return _report(spec, ctx, res, extra_findings=[f"weak sources: {weak}"] if weak else [],
                   data={"source_scores": scores})


@rule("github")
def github(ctx, spec):
    res = {}
    for c in ctx.claims:
        if not any(w in c.text.lower() for w in ("github", "repository", "repo ", "stars", "open-source", "open source")):
            res[c.claim_id] = {"verdict": "na", "note": "not a repository claim"}
            continue
        repo = [s for s in _cited(ctx, c) if "github.com" in s.url or s.source_type == "repository"]
        res[c.claim_id] = ({"verdict": "pass", "note": f"cites repository {repo[0].url} (live GitHub data NOT CONNECTED)"} if repo
                           else {"verdict": "warn", "note": "repository claim without a repository source"})
    return _report(spec, ctx, res)


@rule("paper")
def paper(ctx, spec):
    import re
    res = {}
    for c in ctx.claims:
        if not any(w in c.text.lower() for w in ("paper", "study", "preprint", "arxiv", "researchers found")):
            res[c.claim_id] = {"verdict": "na", "note": "not a paper claim"}
            continue
        ok = [s for s in _cited(ctx, c) if s.source_type == "paper" or re.search(r"arxiv\.org/abs/\d{4}\.\d{4,5}|doi\.org/10\.", s.url)]
        res[c.claim_id] = ({"verdict": "pass", "note": f"cites paper {ok[0].url}"} if ok
                           else {"verdict": "warn", "note": "paper claim without an identifiable paper source"})
    return _report(spec, ctx, res)


@rule("company_announcement")
def company_announcement(ctx, spec):
    res = {}
    for c in ctx.claims:
        if not any(w in c.text.lower() for w in ("announced", "launched", "released", "introduced", "unveiled", "rolled out")):
            res[c.claim_id] = {"verdict": "na", "note": "not an announcement claim"}
            continue
        prim = [s for s in _cited(ctx, c) if s.source_type in ("primary", "official_docs")]
        res[c.claim_id] = ({"verdict": "pass", "note": f"company's own source {prim[0].publisher}"} if prim
                           else {"verdict": "warn", "note": "announcement claim not backed by the company's own source"})
    return _report(spec, ctx, res)
