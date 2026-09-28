"""Knowledge rules (Part 6)."""
from __future__ import annotations

import re
from collections import Counter
from datetime import date, datetime
from itertools import combinations

from aibos import config
from aibos.evidence import evidence_chain, parse_date
from aibos.memory import MemoryError_
from aibos.rules import content_words, out, rule
from aibos.schemas import RunStatus, Verification, to_jsonable


def classify_text(text: str) -> list[str]:
    t = text.lower()
    scores = {cat: sum(t.count(k) for k in kws) for cat, kws in config.taxonomy().items()}
    return [c for c, s in sorted(scores.items(), key=lambda x: -x[1]) if s > 0][:3]


@rule("knowledge_classify")
def knowledge_classify(ctx, spec):
    cls = {c.claim_id: classify_text(c.text) for c in ctx.claims}
    unclassified = [cid for cid, tags in cls.items() if not tags]
    return out(spec, ctx, findings=[f"classified {len(cls) - len(unclassified)}/{len(cls)} claims"],
               uncertainties=[f"unclassified: {unclassified}"] if unclassified else [],
               data={"classifications": cls}, confidence=0.8)


@rule("research_to_knowledge")
def research_to_knowledge(ctx, spec):
    entries, open_q, errors = [], [], []
    for c in ctx.claims:
        tags = classify_text(c.text)
        chain = [to_jsonable(link) for link in evidence_chain(c, ctx.sources)]
        if c.verification == Verification.SUPPORTED:
            entry = {"entry_id": f"k_{c.claim_id}", "title": c.text[:90], "summary": c.text,
                     "claim_ids": [c.claim_id], "tags": tags, "confidence": c.confidence,
                     "status": "VERIFIED", "evidence_chain": chain, "as_of": ctx.today}
            entries.append(entry)
            level, kind = "global", "verified_fact"
        else:
            open_q.append({"claim_id": c.claim_id, "text": c.text, "verification": c.verification.value,
                           "notes": c.verification_notes})
            entry = {"text": c.text, "verification": c.verification.value, "notes": c.verification_notes}
            level, kind = "project", "open_question"
        if ctx.persist:
            try:
                ctx.memory.write(level, kind, entry, tags=tags, source=ctx.run_id)
            except MemoryError_ as exc:
                errors.append(f"{c.claim_id}: {exc}")
    return out(spec, ctx,
               findings=[f"{len(entries)} verified knowledge entries; {len(open_q)} open questions"],
               uncertainties=[f"{q['claim_id']} not verified ({q['verification']})" for q in open_q],
               errors=errors, data={"knowledge": entries, "open_questions": open_q},
               files_changed=["data/memory/global.jsonl", "data/memory/project.jsonl"] if ctx.persist else [],
               confidence=1.0, next_action="use VERIFIED entries as facts; research open questions further")


@rule("knowledge_link")
def knowledge_link(ctx, spec):
    ents = ctx.board.get("knowledge", []) or []
    links = []
    for a, b in combinations(ents, 2):
        shared = content_words(a.get("summary", "")) & content_words(b.get("summary", ""))
        if len(shared) >= 3:
            links.append({"from": a["entry_id"], "to": b["entry_id"], "shared_terms": sorted(shared)[:8]})
    return out(spec, ctx, findings=[f"{len(links)} links"], data={"knowledge_links": links}, confidence=0.7)


@rule("duplicate")
def duplicate(ctx, spec):
    dups = []
    for a, b in combinations(ctx.claims, 2):
        wa, wb = content_words(a.text), content_words(b.text)
        if wa and wb and len(wa & wb) / len(wa | wb) >= 0.8:
            dups.append([a.claim_id, b.claim_id])
    return out(spec, ctx, findings=[f"{len(dups)} near-duplicate claim pairs"], data={"duplicates": dups},
               recommendations=["merge duplicates before publishing"] if dups else [], confidence=0.8)


@rule("taxonomy")
def taxonomy(ctx, spec):
    tax = config.taxonomy()
    counts = Counter(t for c in ctx.claims for t in classify_text(c.text))
    uncl = [c.claim_id for c in ctx.claims if not classify_text(c.text)]
    return out(spec, ctx, findings=[f"taxonomy categories: {len(tax)}", f"usage: {dict(counts)}"],
               recommendations=[f"consider new category for claims {uncl}"] if uncl else [],
               data={"taxonomy_usage": dict(counts)}, confidence=0.8)


@rule("knowledge_gap")
def knowledge_gap(ctx, spec):
    gaps = []
    for c in ctx.claims:
        if c.verification != Verification.SUPPORTED:
            gaps.append({"claim_id": c.claim_id, "gap": f"verification={c.verification.value}"})
        pubs = {s.publisher for sid in c.source_ids if (s := ctx.sources.get(sid))}
        if len(pubs) < 2:
            gaps.append({"claim_id": c.claim_id, "gap": "single publisher; needs independent corroboration"})
    for s in ctx.sources.all():
        if not parse_date(s.published):
            gaps.append({"source_id": s.source_id, "gap": "missing publication date"})
    return out(spec, ctx, findings=[f"{len(gaps)} knowledge gaps"], data={"knowledge_gaps": gaps},
               next_action="research the gaps before relying on those claims", confidence=0.9)


@rule("outdated_knowledge")
def outdated_knowledge(ctx, spec):
    stale = int(spec.params.get("stale_days", 180))
    today = date.fromisoformat(ctx.today)
    old = []
    for r in ctx.memory.read("global", kind="verified_fact"):
        as_of = r["content"].get("as_of") or r.get("written_at", "")[:10]
        try:
            age = (today - datetime.fromisoformat(as_of).date()).days
        except ValueError:
            continue
        if age > stale:
            old.append({"id": r["id"], "title": r["content"].get("title"), "age_days": age})
    return out(spec, ctx, findings=[f"{len(old)} stale knowledge entries (> {stale} days)"],
               data={"stale_knowledge": old}, confidence=0.9,
               next_action="re-verify stale entries" if old else "none")


@rule("terminology")
def terminology(ctx, spec):
    text = " ".join(s.text for s in ctx.sources.all()) + " " + " ".join(c.text for c in ctx.claims)
    acronyms = Counter(re.findall(r"\b[A-Z]{2,6}s?\b", text))
    phrases = Counter(re.findall(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z0-9]+)+)\b", text))
    terms = [t for t, n in (acronyms + phrases).most_common(40) if n >= 2]
    return out(spec, ctx, findings=[f"{len(terms)} candidate glossary terms"], data={"terms": terms}, confidence=0.6)


@rule("prerequisites")
def prerequisites(ctx, spec):
    missing = []
    for a in ctx.board.get("explanations", []) or []:
        glossary = {k.lower() for k in (a.get("glossary") or {})}
        terms = set(re.findall(r"\b[A-Z]{2,6}\b", a.get("text", "")))
        undefined = [t for t in terms if t.lower() not in glossary and f"{t} (" not in a.get("text", "")]
        if undefined:
            missing.append({"artifact_id": a.get("artifact_id"), "undefined_terms": sorted(undefined)})
    return out(spec, ctx, findings=[f"{len(missing)} explanations use undefined acronyms"],
               data={"prerequisites": missing}, status=RunStatus.OK, confidence=0.7)
