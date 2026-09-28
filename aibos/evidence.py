"""Evidence system (Part 27): sources, claims, verification aggregation and
evidence chains. Assumptions are never silently promoted to facts: a claim
becomes FACT only when verification aggregates to SUPPORTED."""
from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from aibos import paths
from aibos.schemas import (Claim, ClaimKind, EvidenceLink, Source, Verification,
                           to_jsonable)
from aibos.store import read_json, write_json

SOURCE_TIER = {           # higher = stronger evidence
    "primary": 1.0,         # the originating organisation's own announcement / release
    "official_docs": 0.95,
    "paper": 0.9,
    "repository": 0.85,
    "news": 0.65,
    "analysis": 0.55,
    "blog": 0.45,
    "social": 0.3,
    "unknown": 0.2,
}
PRIMARY_TYPES = {"primary", "official_docs", "paper", "repository"}


def normalize(text: str) -> str:
    text = (text or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_in_text(quote: str, text: str) -> bool:
    q = normalize(quote).strip(" .\"'")
    return bool(q) and q in normalize(text)


def parse_date(s: str) -> date | None:
    if not s:
        return None
    s = s.strip()
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        pass
    for fmt in ("%Y-%m", "%B %d, %Y", "%b %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def claim_from_dict(d: dict[str, Any]) -> Claim:
    d = dict(d)
    d["kind"] = ClaimKind(d.get("kind", "ASSUMPTION"))
    d["verification"] = Verification(d.get("verification", "UNVERIFIED"))
    allowed = set(Claim.__dataclass_fields__)
    return Claim(**{k: v for k, v in d.items() if k in allowed})


def source_from_dict(d: dict[str, Any]) -> Source:
    allowed = set(Source.__dataclass_fields__)
    return Source(**{k: v for k, v in d.items() if k in allowed})


class SourceStore:
    """Captured sources. Content is whatever was actually retrieved — never generated."""

    def __init__(self, sources: Iterable[Source] = ()):
        self._by_id: dict[str, Source] = {s.source_id: s for s in sources}

    @classmethod
    def from_file(cls, path: str | Path) -> "SourceStore":
        raw = read_json(Path(path), default=[])
        items = raw.get("sources", raw) if isinstance(raw, dict) else raw
        return cls(source_from_dict(d) for d in items)

    @classmethod
    def persistent(cls) -> "SourceStore":
        return cls.from_file(paths.sub("sources") / "sources.json")

    def save_persistent(self) -> Path:
        p = paths.sub("sources") / "sources.json"
        write_json(p, [to_jsonable(s) for s in self._by_id.values()])
        return p

    def add(self, s: Source) -> None:
        self._by_id[s.source_id] = s

    def remove(self, source_id: str) -> None:
        self._by_id.pop(source_id, None)

    def get(self, source_id: str) -> Source | None:
        return self._by_id.get(source_id)

    def all(self) -> list[Source]:
        return list(self._by_id.values())

    def __len__(self) -> int:
        return len(self._by_id)


def aggregate_verification(claims: list[Claim], reports: list[dict[str, Any]],
                           sources: SourceStore) -> list[Claim]:
    """Combine verifier verdicts into one verification status per claim.

    Verdicts per verifier: pass | fail | warn | na.
    - any 'contradiction' fail           -> CONTRADICTED
    - any hard fail (citation, primary quote, quote, statistics) -> UNSUPPORTED
    - no hard fails, >=1 pass, no warns  -> SUPPORTED
    - otherwise                          -> PARTIALLY_SUPPORTED
    Only SUPPORTED claims become FACT; confidence blends source tier and verdicts.
    """
    hard = {"verification.citation", "verification.primary_source", "verification.quote",
            "verification.statistics", "verification.claim"}
    per_claim: dict[str, list[tuple[str, str, str]]] = {c.claim_id: [] for c in claims}
    for rep in reports:
        agent = rep.get("agent_id", "")
        for cid, res in (rep.get("results") or {}).items():
            if cid in per_claim:
                per_claim[cid].append((agent, res.get("verdict", "na"), res.get("note", "")))
    for c in claims:
        verdicts = per_claim.get(c.claim_id, [])
        c.verification_notes = [f"{a}: {v.upper()} — {n}" for a, v, n in verdicts]
        fails = [(a, v) for a, v, _ in verdicts if v == "fail"]
        warns = [a for a, v, _ in verdicts if v == "warn"]
        passes = [a for a, v, _ in verdicts if v == "pass"]
        if any(a == "verification.contradiction" for a, _ in fails):
            c.verification = Verification.CONTRADICTED
        elif any(a in hard for a, _ in fails):
            c.verification = Verification.UNSUPPORTED
        elif passes and not warns and not fails:
            c.verification = Verification.SUPPORTED
        elif passes:
            c.verification = Verification.PARTIALLY_SUPPORTED
        else:
            c.verification = Verification.UNVERIFIED
        tiers = [SOURCE_TIER.get(s.source_type, 0.2) for sid in c.source_ids if (s := sources.get(sid))]
        base = max(tiers) if tiers else 0.0
        publishers = {sources.get(sid).publisher for sid in c.source_ids if sources.get(sid)}
        corroboration = min(1.0, 0.8 + 0.1 * len(publishers)) if publishers else 0.0
        factor = {Verification.SUPPORTED: 1.0, Verification.PARTIALLY_SUPPORTED: 0.7,
                  Verification.UNVERIFIED: 0.3, Verification.UNSUPPORTED: 0.1,
                  Verification.CONTRADICTED: 0.05}[c.verification]
        c.confidence = round(base * corroboration * factor, 3)
        if c.verification == Verification.SUPPORTED:
            c.kind = ClaimKind.FACT
        elif c.kind == ClaimKind.FACT:
            # Guard: an agent labelled this FACT but evidence does not support it.
            c.kind = ClaimKind.ASSUMPTION
            c.verification_notes.append("evidence-guard: downgraded FACT -> ASSUMPTION (not verified)")
    return claims


def evidence_chain(claim: Claim, sources: SourceStore, interpretation: str = "",
                   decision: str = "") -> list[EvidenceLink]:
    links = []
    for i, sid in enumerate(claim.source_ids or ["(none)"]):
        s = sources.get(sid)
        quote = claim.quotes[i] if i < len(claim.quotes) else (claim.quotes[0] if claim.quotes else "")
        links.append(EvidenceLink(
            claim=claim.text,
            source=f"{s.publisher} — {s.title} ({s.url}, {s.published or 'date unknown'})" if s else "NO SOURCE",
            evidence=quote or "NO QUOTED EVIDENCE",
            confidence=claim.confidence,
            interpretation=interpretation or f"{claim.verification.value}; kind={claim.kind.value}",
            decision=decision or ("usable as fact" if claim.kind == ClaimKind.FACT
                                  else "use only as hypothesis / needs verification"),
        ))
    return links
