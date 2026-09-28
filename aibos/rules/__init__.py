"""Deterministic ("rule") agent implementations.

Rule agents are cheap, explainable and testable. Each is a function
`(ctx, spec) -> AgentOutput` registered under the name used in the registry's
`executor: rule:<name>` field. Many registry agents share one rule with
different `params` (e.g. all metric analysts use rule:metrics).
"""
from __future__ import annotations

import re
from typing import Callable

from aibos.schemas import AgentOutput, AgentSpec, RunStatus

RuleFn = Callable[["RunContext", AgentSpec], AgentOutput]  # noqa: F821
RULES: dict[str, RuleFn] = {}


def rule(name: str):
    def deco(fn: RuleFn) -> RuleFn:
        RULES[name] = fn
        return fn
    return deco


def out(spec: AgentSpec, ctx, **kw) -> AgentOutput:
    kw.setdefault("status", RunStatus.OK)
    kw.setdefault("backend", "rule")
    kw.setdefault("provenance", f"deterministic rule {spec.executor}")
    return AgentOutput(agent_id=spec.agent_id, task=kw.pop("task", spec.purpose), **kw)


STOPWORDS = set("""a an the and or but if of to in on for with at by from as is are was were be been being it its
this that these those which who whom what when where why how not no can will would should could may might
has have had do does did than then so such into about over under also more most very just their there they
them our we you your i he she his her per via up out new""".split())

NUMBER_RE = re.compile(r"(?<![\w.\-])(?:\$|€|£)?\d[\d,]*(?:\.\d+)?(?:\s?%|\s?(?:million|billion|trillion|k|m|bn|x)\b)?", re.I)


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9'\-]*", (text or "").lower())


def content_words(text: str) -> set[str]:
    return {w for w in words(text) if w not in STOPWORDS and len(w) > 2}


def numbers_in(text: str) -> list[str]:
    """Numbers as they appear, normalised (commas removed, lowercase)."""
    out = []
    for m in NUMBER_RE.finditer(text or ""):
        tok = m.group(0).strip().lower().replace(",", "")
        core = re.sub(r"[^\d.]", "", tok)
        if not core or core == ".":
            continue
        out.append(core.rstrip("."))
    return out


def artifacts(ctx) -> list[dict]:
    """All draft artifacts that quality agents should score."""
    items = []
    for key in ("content", "explanations", "scripts"):
        for a in ctx.board.get(key, []) or []:
            if isinstance(a, dict) and a.get("text"):
                a.setdefault("artifact_id", f"{key}-{len(items) + 1}")
                a.setdefault("platform", a.get("level", key))
                items.append(a)
    return items


# Import rule modules so they register themselves.
from aibos.rules import verification, knowledge, content_quality, security_rules, analytics_rules, ops, teaching  # noqa: E402,F401
