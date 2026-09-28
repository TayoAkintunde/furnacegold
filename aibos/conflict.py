"""Conflict resolution (Part 28).

1. identify the disagreement  2. gather evidence for each position
3. identify uncertainty       4. prefer primary evidence
5. request another specialist when needed  6. preserve disagreement if unresolved.
Never forces artificial consensus.
"""
from __future__ import annotations

from typing import Any


# Checks that examine the claim's content against source text. A substantiated failure from one of
# these outweighs passes from checks that looked at other aspects (conservative by design).
CONTENT_CHECKS = {"verification.primary_source", "verification.quote", "verification.statistics",
                  "verification.citation", "verification.contradiction", "verification.claim"}


def resolve(description: str, positions: list[dict[str, Any]], tie_breaker_agent: str | None = None) -> dict[str, Any]:
    """positions: [{agent, stance, evidence, evidence_strength (0-1)}]"""
    ranked = sorted(positions, key=lambda p: -p.get("evidence_strength", 0))
    if len(ranked) >= 2 and ranked[0].get("evidence_strength", 0) - ranked[1].get("evidence_strength", 0) >= 0.2:
        resolution = (f"RESOLVED in favour of {ranked[0]['agent']} ({ranked[0]['stance']}): stronger/primary evidence "
                      f"({ranked[0].get('evidence_strength')} vs {ranked[1].get('evidence_strength')})")
        status = "RESOLVED"
    else:
        resolution = "PRESERVED: evidence is comparable; disagreement kept and flagged as uncertainty"
        if tie_breaker_agent:
            resolution += f"; recommended extra verification by {tie_breaker_agent}"
        status = "PRESERVED"
    return {"description": description, "positions": positions, "status": status, "resolution": resolution}


def from_verification(ctx) -> list[dict[str, Any]]:
    conflicts = []
    reports = ctx.board.get("verification_reports", []) or []
    for c in ctx.claims:
        positions = []
        for rep in reports:
            r = (rep.get("results") or {}).get(c.claim_id)
            if r and r["verdict"] in ("pass", "fail"):
                agent = rep["agent_id"]
                strength = (1.0 if agent in CONTENT_CHECKS else 0.5) if r["verdict"] == "fail" else 0.6
                positions.append({"agent": agent, "stance": r["verdict"], "evidence": r["note"], "evidence_strength": strength})
        stances = {p["stance"] for p in positions}
        if stances == {"pass", "fail"}:
            fails = [p for p in positions if p["stance"] == "fail"]
            passes = [p for p in positions if p["stance"] == "pass"]
            best_fail = max(fails, key=lambda p: p["evidence_strength"])
            best_pass = max(passes, key=lambda p: p["evidence_strength"])
            conflicts.append(resolve(f"verifiers disagree on {c.claim_id}", [best_fail, best_pass],
                                     tie_breaker_agent="verification.cross_source"))
    for con in ctx.board.get("contradictions", []) or []:
        conflicts.append({"description": con["note"], "positions": con["claims"],
                          "status": "RESOLVED" if "kept" in con.get("resolution", "") else "PRESERVED",
                          "resolution": con.get("resolution", "")})
    return conflicts
