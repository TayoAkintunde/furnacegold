"""Content quality rules (Part 9). Each scores every draft artifact and emits
issues with severity BLOCKING | WARN | INFO. BLOCKING keeps a draft out of the
approval queue until fixed."""
from __future__ import annotations

import re
from collections import Counter

from aibos import config
from aibos.evidence import normalize
from aibos.rules import artifacts, numbers_in, out, rule, words
from aibos.schemas import Verification

AI_SLOP = ["in today's fast-paced", "delve", "unlock the power", "unleash", "game-changer", "game changer",
           "it's important to note", "it is important to note", "in conclusion", "revolutionize",
           "ever-evolving", "tapestry", "harness the power", "elevate your", "seamlessly", "cutting-edge",
           "in the realm of", "navigate the complexities", "a testament to", "look no further",
           "embark on a journey", "supercharge"]
HYPE = ["revolutionary", "game-changing", "unprecedented", "mind-blowing", "insane", "never before seen",
        "changes everything", "10x", "100x", "the best ever", "world's first", "magic", "skyrocket"]
FINANCIAL_PROMISES = [r"guarantee[ds]?", r"get rich", r"passive income", r"make \$\d", r"earn \$\d",
                      r"risk[- ]free", r"quit your job", r"financial freedom"]
CLICKBAIT = [r"you won'?t believe", r"this one (weird )?trick", r"shocking", r"what happens next",
             r"will blow your mind", r"doctors hate", r"number \d+ will", r"nobody is talking about"]
MANIPULATIVE_CTA = [r"only today", r"last chance", r"act now", r"before it'?s too late", r"hurry",
                    r"only \d+ (spots|seats) left"]
CTA = [r"\bsubscribe\b", r"\bfollow\b", r"\bsign up\b", r"\bjoin\b", r"\bcomment\b", r"\breply\b",
       r"\bdownload\b", r"\bregister\b", r"\bbook a\b", r"\bread more\b", r"\bshare\b"]


def _report(spec, ctx, reports: list[dict]):
    blocking = sum(1 for r in reports for i in r["issues"] if i["severity"] == "BLOCKING")
    warns = sum(1 for r in reports for i in r["issues"] if i["severity"] == "WARN")
    avg = round(sum(r["score"] for r in reports) / len(reports), 3) if reports else None
    return out(spec, ctx, findings=[f"{spec.name}: {len(reports)} drafts, {blocking} blocking, {warns} warnings, avg score {avg}"],
               data={"quality_reports": reports}, confidence=1.0 if reports else 0.0,
               uncertainties=[] if reports else ["no drafts to evaluate"],
               tests_performed=[spec.focus])


def _rep(spec, a, score, issues):
    return {"artifact_id": a["artifact_id"], "agent_id": spec.agent_id, "score": round(max(0.0, min(1.0, score)), 3),
            "issues": issues}


def _issue(sev, msg):
    return {"severity": sev, "message": msg}


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if len(words(p)) >= 3]


def syllables(word: str) -> int:
    w = word.lower().strip("'")
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def flesch(text: str) -> tuple[float, float]:
    sents = sentences(text) or [text]
    ws = words(text)
    if not ws:
        return 0.0, 0.0
    syl = sum(syllables(w) for w in ws)
    wps = len(ws) / len(sents)
    spw = syl / len(ws)
    return round(206.835 - 1.015 * wps - 84.6 * spw, 1), round(0.39 * wps + 11.8 * spw - 15.59, 1)


def _count(patterns, text):
    t = text.lower()
    return [p for p in patterns if re.search(p, t)]


@rule("hook")
def hook(ctx, spec):
    reps = []
    for a in artifacts(ctx):
        first = next((line for line in a["text"].splitlines() if line.strip()), "")
        n = len(words(first))
        specific = bool(numbers_in(first)) or bool(re.search(r"\b[A-Z][a-z]+", first[1:]))
        issues = []
        if n > 25:
            issues.append(_issue("WARN", f"opening line is {n} words; make the point sooner"))
        if not specific:
            issues.append(_issue("INFO", "opening line has no specific detail (name, number, concrete outcome)"))
        if first.strip().endswith("?") and n < 6:
            issues.append(_issue("INFO", "very short question hook; ensure it is not a curiosity gap"))
        reps.append(_rep(spec, a, 1 - 0.4 * (n > 25) - 0.2 * (not specific), issues))
    return _report(spec, ctx, reps)


@rule("clarity")
def clarity(ctx, spec):
    reps = []
    for a in artifacts(ctx):
        sents = sentences(a["text"])
        long = [s for s in sents if len(words(s)) > 35]
        passive = len(re.findall(r"\b(?:is|are|was|were|be|been|being)\s+\w+ed\b", a["text"]))
        issues = []
        if long:
            issues.append(_issue("WARN", f"{len(long)} sentence(s) over 35 words"))
        if sents and passive / len(sents) > 0.3:
            issues.append(_issue("INFO", "heavy passive voice"))
        reps.append(_rep(spec, a, 1 - 0.1 * len(long) - 0.1 * (passive / max(len(sents), 1) > 0.3), issues))
    return _report(spec, ctx, reps)


@rule("readability")
def readability(ctx, spec):
    reps = []
    for a in artifacts(ctx):
        ease, grade = flesch(a["text"])
        level = a.get("level", "general")
        target = 55 if level == "beginner" else 40 if level in ("general", "intermediate") else 25
        issues = [_issue("INFO", f"Flesch reading ease {ease}, grade {grade} (target >= {target} for {level})")]
        if ease < target:
            issues.append(_issue("WARN", f"reading ease {ease} below target {target}"))
        reps.append(_rep(spec, a, min(1.0, max(0.0, ease) / target) if target else 1.0, issues))
    return _report(spec, ctx, reps)


@rule("educational_value")
def educational_value(ctx, spec):
    reps = []
    for a in artifacts(ctx):
        t = a["text"].lower()
        has_def = bool(re.search(r"\b(is a|is an|means|refers to|think of it as|in plain terms)\b", t)) or bool(a.get("glossary"))
        has_example = bool(re.search(r"\b(for example|e\.g\.|for instance|imagine|like a|such as)\b", t))
        has_takeaway = bool(a.get("takeaways")) or bool(re.search(r"(takeaway|key point|in short|what this means|try this|step \d|^\s*[-*\d]+[.)]?\s)", t, re.M))
        score = (has_def + has_example + has_takeaway) / 3
        issues = [] if score >= 0.67 else [_issue("WARN", f"teaches little: definition={has_def}, example={has_example}, takeaway={has_takeaway}")]
        reps.append(_rep(spec, a, score, issues))
    return _report(spec, ctx, reps)


def _ngrams(text: str, n: int) -> set[tuple[str, ...]]:
    ws = words(text)
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


@rule("originality")
def originality(ctx, spec):
    arts = artifacts(ctx)
    src = set().union(*[_ngrams(s.text, 6) for s in ctx.sources.all()]) if len(ctx.sources) else set()
    reps = []
    for a in arts:
        g = _ngrams(a["text"], 6)
        from_src = len(g & src) / len(g) if g else 0
        cross = max((len(g & _ngrams(b["text"], 6)) / len(g) for b in arts if b is not a and g), default=0)
        issues = []
        if from_src > 0.3:
            issues.append(_issue("WARN", f"{from_src:.0%} of 6-grams copied from sources"))
        if cross > 0.5:
            issues.append(_issue("WARN", f"{cross:.0%} overlap with another draft — not platform-native"))
        reps.append(_rep(spec, a, 1 - max(from_src, cross), issues))
    return _report(spec, ctx, reps)


@rule("factuality")
def factuality(ctx, spec):
    by_id = {c.claim_id: c for c in ctx.claims}
    reps = []
    for a in artifacts(ctx):
        ids = a.get("claim_ids") or []
        issues = []
        unknown = [i for i in ids if i not in by_id]
        unverified = [i for i in ids if i in by_id and by_id[i].verification != Verification.SUPPORTED]
        if unknown:
            issues.append(_issue("BLOCKING", f"references unknown claims {unknown}"))
        if unverified:
            issues.append(_issue("BLOCKING", "relies on unverified claims " +
                                 ", ".join(f"{i}({by_id[i].verification.value})" for i in unverified)))
        if not ids and numbers_in(a["text"]):
            issues.append(_issue("WARN", "states numbers but references no claim ids"))
        reps.append(_rep(spec, a, 0.0 if any(i["severity"] == "BLOCKING" for i in issues) else 1.0 - 0.3 * bool(issues), issues))
    return _report(spec, ctx, reps)


@rule("source_attribution")
def source_attribution(ctx, spec):
    pubs = [s.publisher.lower() for s in ctx.sources.all()]
    reps = []
    for a in artifacts(ctx):
        t = a["text"].lower()
        attributed = ("http" in t or "source" in t or "according to" in t or any(p and p in t for p in pubs))
        issues = [] if attributed or not numbers_in(a["text"]) else [_issue("WARN", "factual numbers without visible attribution")]
        reps.append(_rep(spec, a, 1.0 if not issues else 0.6, issues))
    return _report(spec, ctx, reps)


@rule("brand_voice")
def brand_voice(ctx, spec):
    b = config.brand()
    reps = []
    for a in artifacts(ctx):
        t = a["text"]
        bad = [p for p in b.get("avoid_phrases", []) if p.lower() in t.lower()]
        excl = t.count("!")
        emoji = len(re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", t))
        issues = []
        if bad:
            issues.append(_issue("WARN", f"off-brand phrases: {bad}"))
        if excl > b.get("max_exclamation_marks", 1):
            issues.append(_issue("WARN", f"{excl} exclamation marks"))
        if emoji > b.get("max_emoji", 3):
            issues.append(_issue("WARN", f"{emoji} emoji"))
        reps.append(_rep(spec, a, 1 - 0.2 * len(issues), issues))
    return _report(spec, ctx, reps)


@rule("cta")
def cta(ctx, spec):
    reps = []
    for a in artifacts(ctx):
        t = a["text"] + " " + str(a.get("cta", ""))
        ctas = _count(CTA, t)
        manip = _count(MANIPULATIVE_CTA, t)
        issues = []
        if manip:
            issues.append(_issue("BLOCKING", f"manipulative urgency: {manip}"))
        if len(ctas) > 2:
            issues.append(_issue("WARN", f"{len(ctas)} different calls to action; keep one"))
        if not ctas and not a.get("cta"):
            issues.append(_issue("INFO", "no call to action"))
        reps.append(_rep(spec, a, 0.0 if manip else 1 - 0.2 * (len(ctas) > 2), issues))
    return _report(spec, ctx, reps)


@rule("repetition")
def repetition(ctx, spec):
    reps = []
    for a in artifacts(ctx):
        sents = [normalize(s) for s in sentences(a["text"])]
        dup_s = [s for s, n in Counter(sents).items() if n > 1]
        tri = Counter(tuple(words(a["text"])[i:i + 3]) for i in range(max(0, len(words(a["text"])) - 2)))
        rep3 = [" ".join(k) for k, n in tri.items() if n >= 4 and not set(k) <= {"the", "of", "and", "to", "a"}]
        issues = []
        if dup_s:
            issues.append(_issue("WARN", f"{len(dup_s)} repeated sentence(s)"))
        if rep3:
            issues.append(_issue("INFO", f"repeated phrases: {rep3[:3]}"))
        reps.append(_rep(spec, a, 1 - 0.3 * bool(dup_s) - 0.1 * bool(rep3), issues))
    return _report(spec, ctx, reps)


@rule("ai_slop")
def ai_slop(ctx, spec):
    reps = []
    for a in artifacts(ctx):
        hits = [p for p in AI_SLOP if p in a["text"].lower()]
        issues = [_issue("WARN" if len(hits) < 4 else "BLOCKING", f"generic AI phrases: {hits}")] if hits else []
        reps.append(_rep(spec, a, 1 - 0.15 * len(hits), issues))
    return _report(spec, ctx, reps)


@rule("hype")
def hype(ctx, spec):
    reps = []
    for a in artifacts(ctx):
        t = a["text"].lower()
        h = [p for p in HYPE if p in t]
        money = [p for p in FINANCIAL_PROMISES if re.search(p, t)]
        issues = []
        if money:
            issues.append(_issue("BLOCKING", f"financial-success promise: {money}"))
        if h:
            issues.append(_issue("WARN", f"hype words: {h}"))
        reps.append(_rep(spec, a, 0.0 if money else 1 - 0.2 * len(h), issues))
    return _report(spec, ctx, reps)


@rule("clickbait")
def clickbait(ctx, spec):
    reps = []
    for a in artifacts(ctx):
        t = a["text"] + " " + a.get("title", "")
        hits = [p for p in CLICKBAIT if re.search(p, t.lower())]
        caps = [w for w in re.findall(r"\b[A-Z]{4,}\b", t) if w not in {"HTTP", "HTTPS", "JSON", "NASA", "GDPR"}]
        issues = []
        if hits:
            issues.append(_issue("BLOCKING", f"clickbait patterns: {hits}"))
        if len(caps) > 3:
            issues.append(_issue("WARN", f"shouting caps: {caps[:5]}"))
        reps.append(_rep(spec, a, 0.0 if hits else 1 - 0.2 * (len(caps) > 3), issues))
    return _report(spec, ctx, reps)


@rule("hallucination")
def hallucination(ctx, spec):
    allowed_nums = set()
    verified = [c for c in ctx.claims if c.verification == Verification.SUPPORTED]
    for c in verified:
        allowed_nums |= set(numbers_in(c.text))
        for sid in c.source_ids:
            if (s := ctx.sources.get(sid)):
                allowed_nums |= set(numbers_in(normalize(s.text).replace(",", "")))
    reps = []
    for a in artifacts(ctx):
        text = re.sub(r"https?://\S+", " ", a["text"])            # URLs are not claims
        text = re.sub(r"(?m)^\s*\d+[/.)]\s*", " ", text)            # list / thread numbering "1/" "2."
        nums = [n for n in numbers_in(text) if n not in allowed_nums]
        issues = [_issue("BLOCKING", f"numbers not found in verified claims or their sources: {sorted(set(nums))}")] if nums else []
        reps.append(_rep(spec, a, 0.0 if nums else 1.0, issues))
    return _report(spec, ctx, reps)


@rule("plagiarism")
def plagiarism(ctx, spec):
    reps = []
    srcs = [words(s.text) for s in ctx.sources.all()]
    src_grams = set()
    for ws in srcs:
        src_grams |= {tuple(ws[i:i + 12]) for i in range(len(ws) - 11)}
    for a in artifacts(ctx):
        unquoted = re.sub(r'"[^"]*"|“[^”]*”', " ", a["text"])
        ws = words(unquoted)
        hits = sum(1 for i in range(len(ws) - 11) if tuple(ws[i:i + 12]) in src_grams)
        issues = []
        if hits >= 14:
            issues.append(_issue("BLOCKING", "25+ word verbatim run copied from a source without quotation marks"))
        elif hits:
            issues.append(_issue("WARN", "12+ word verbatim run copied from a source; quote or paraphrase it"))
        reps.append(_rep(spec, a, 1 - min(1.0, hits / 14), issues))
    return _report(spec, ctx, reps)


@rule("platform_fit")
def platform_fit(ctx, spec):
    plats = config.platforms()
    reps = []
    for a in artifacts(ctx):
        p = plats.get(a.get("platform", ""))
        if not p:
            reps.append(_rep(spec, a, 1.0, [_issue("INFO", f"no platform rules for '{a.get('platform')}'")]))
            continue
        t = a["text"]
        issues = []
        nch, nw = len(t), len(words(t))
        if "max_chars" in p and nch > p["max_chars"]:
            issues.append(_issue("BLOCKING", f"{nch} chars > {p['max_chars']} limit"))
        if "min_chars" in p and nch < p["min_chars"]:
            issues.append(_issue("WARN", f"{nch} chars < suggested minimum {p['min_chars']}"))
        if "max_words" in p and nw > p["max_words"]:
            issues.append(_issue("BLOCKING", f"{nw} words > {p['max_words']} limit"))
        if "min_words" in p and nw < p["min_words"]:
            issues.append(_issue("WARN", f"{nw} words < suggested minimum {p['min_words']}"))
        sep = p.get("part_separator")
        if sep:
            parts = [x.strip() for x in re.split(r"\n\s*---\s*\n", t) if x.strip()]
            lim = p.get("max_chars_per_part") or p.get("max_chars_per_slide")
            over = [i + 1 for i, x in enumerate(parts) if lim and len(x) > lim]
            if over:
                issues.append(_issue("BLOCKING", f"parts {over} exceed {lim} chars"))
            if p.get("min_parts") and len(parts) < p["min_parts"]:
                issues.append(_issue("WARN", f"{len(parts)} parts < {p['min_parts']}"))
            mx = p.get("max_parts") or p.get("max_slides")
            if mx and len(parts) > mx:
                issues.append(_issue("BLOCKING", f"{len(parts)} parts > {mx}"))
        blocking = any(i["severity"] == "BLOCKING" for i in issues)
        reps.append(_rep(spec, a, 0.0 if blocking else 1 - 0.1 * len(issues), issues))
    return _report(spec, ctx, reps)
