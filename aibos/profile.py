"""Business profile (config/business_profile.yaml): load, completeness, validation.

Empty values mean UNKNOWN. This module never fills in defaults. Agents must
treat unknown fields as unknown, not guess them.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from aibos import config, security
from aibos.paths import CONFIG_DIR

PROFILE_PATH = CONFIG_DIR / "business_profile.yaml"
META_KEYS = {"profile_version", "profile_status", "last_updated"}

ENUMS = {
    ("business", "stage"): {"idea", "side_project", "early", "established", "other"},
    ("content_style", "formality"): {"casual", "conversational", "professional", "academic"},
    ("content_style", "humour"): {"none", "light", "frequent"},
    ("content_style", "emoji"): {"none", "sparing", "frequent"},
    ("content_style", "preferred_length"): {"short", "medium", "long", "varies_by_platform"},
    ("technology_preferences", "build_approach"): {"no_code", "low_code", "code", "mixed"},
}
LEVELS = {"beginner", "intermediate", "advanced", "expert"}
SOPHISTICATION = {"beginner", "intermediate", "advanced", "mixed"}
EVIDENCE = {"data", "conversations", "assumption"}
BUYING = {"individual", "small_business", "mid_market", "enterprise", "mixed"}


@dataclass
class ProfileReport:
    sections: dict[str, dict[str, int]] = field(default_factory=dict)   # section -> {filled, total}
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        filled = [s for s, v in self.sections.items() if v["filled"]]
        if not filled:
            return "NOT_ANSWERED"
        return "ANSWERED" if len(filled) == len(self.sections) else "PARTIAL"

    @property
    def missing_sections(self) -> list[str]:
        return [s for s, v in self.sections.items() if not v["filled"]]


def load(path: Path | None = None) -> dict[str, Any]:
    p = Path(path or PROFILE_PATH)
    return yaml.safe_load(p.read_text()) or {} if p.exists() else {}


def _empty(v: Any) -> bool:
    return v is None or v == "" or v == [] or v == {}


def _leaves(v: Any) -> list[Any]:
    if isinstance(v, dict):
        return [x for val in v.values() for x in _leaves(val)] if v else [None]
    if isinstance(v, list):
        return [v] if not v else [v]            # a list counts as one leaf (answered if non-empty)
    return [v]


def is_configured(profile: dict[str, Any] | None = None) -> bool:
    return check(profile if profile is not None else load()).status != "NOT_ANSWERED"


def check(profile: dict[str, Any]) -> ProfileReport:
    rep = ProfileReport()
    for section, value in profile.items():
        if section in META_KEYS:
            continue
        leaves = _leaves(value)
        rep.sections[section] = {"filled": sum(not _empty(x) for x in leaves), "total": len(leaves)}
    _validate(profile, rep)
    return rep


def _validate(p: dict[str, Any], rep: ProfileReport) -> None:
    err, warn = rep.errors.append, rep.warnings.append
    for (sec, key), allowed in ENUMS.items():
        v = (p.get(sec) or {}).get(key)
        if not _empty(v) and v not in allowed:
            err(f"{sec}.{key}: '{v}' not one of {sorted(allowed)}")

    for i, a in enumerate((p.get("expertise") or {}).get("areas") or []):
        if a.get("level") and a["level"] not in LEVELS:
            err(f"expertise.areas[{i}].level: '{a['level']}' not one of {sorted(LEVELS)}")

    for i, s in enumerate((p.get("target_audience") or {}).get("segments") or []):
        for key, allowed in (("sophistication", SOPHISTICATION), ("evidence", EVIDENCE), ("buying_power", BUYING)):
            if s.get(key) and s[key] not in allowed:
                err(f"target_audience.segments[{i}].{key}: '{s[key]}' not one of {sorted(allowed)}")
        if s.get("evidence") == "assumption":
            warn(f"target_audience.segments[{i}] is an assumption — agents will treat it as a hypothesis to validate")

    plats = set(config.platforms())
    cp = p.get("content_platforms") or {}
    for i, e in enumerate(cp.get("platforms") or []):
        if e.get("platform") not in plats:
            err(f"content_platforms.platforms[{i}].platform: '{e.get('platform')}' not one of {sorted(plats)}")
        if e.get("priority") is not None and not (isinstance(e["priority"], int) and 1 <= e["priority"] <= 5):
            err(f"content_platforms.platforms[{i}].priority must be an integer 1-5")
    for x in cp.get("platforms_to_avoid") or []:
        if x not in plats:
            warn(f"content_platforms.platforms_to_avoid: '{x}' is not a known platform key")
    both = {e.get("platform") for e in cp.get("platforms") or []} & set(cp.get("platforms_to_avoid") or [])
    if both:
        err(f"platforms both preferred and avoided: {sorted(both)}")

    models = set(config.revenue_streams())
    bm = p.get("preferred_business_models") or {}
    for k in (bm.get("ranked") or []) + (bm.get("excluded") or []):
        if k not in models:
            err(f"preferred_business_models: '{k}' not one of {sorted(models)}")
    clash = set(bm.get("ranked") or []) & set(bm.get("excluded") or [])
    if clash:
        err(f"business models both ranked and excluded: {sorted(clash)}")

    for sec, keys in (("revenue_goals", ("current_monthly_revenue", "target_monthly_revenue_12m",
                                         "minimum_viable_monthly_revenue")),
                      ("budget", ("monthly_total", "tools", "paid_advertising", "contractors", "max_per_experiment"))):
        for k in keys:
            v = (p.get(sec) or {}).get(k)
            if v is not None and (not isinstance(v, (int, float)) or v < 0):
                err(f"{sec}.{k} must be a non-negative number")
    b = p.get("budget") or {}
    parts = [b.get(k) for k in ("tools", "paid_advertising", "contractors") if isinstance(b.get(k), (int, float))]
    if isinstance(b.get("monthly_total"), (int, float)) and sum(parts) > b["monthly_total"]:
        warn("budget: tools + paid_advertising + contractors exceeds monthly_total")

    t = p.get("available_time") or {}
    total = t.get("hours_per_week_total")
    if total is not None and (not isinstance(total, (int, float)) or not 0 <= total <= 168):
        err("available_time.hours_per_week_total must be a number between 0 and 168")
    split = [v for v in (t.get("hours_per_week") or {}).values() if isinstance(v, (int, float))]
    if isinstance(total, (int, float)) and sum(split) > total:
        warn("available_time: split hours exceed hours_per_week_total")

    known = {str(x).lower() for x in (p.get("topics_to_be_known_for") or {}).get("topics") or []}
    avoid = {str(x.get("topic") if isinstance(x, dict) else x).lower()
             for x in (p.get("topics_to_avoid") or {}).get("topics") or []}
    if known & avoid:
        err(f"topics both 'known for' and 'avoid': {sorted(known & avoid)}")

    blob = json.dumps(p, default=str)
    pii = security.scan_pii(blob) + [f for f in security.scan_secrets(blob) if f]
    if pii:
        err(f"profile contains personal data or secrets ({', '.join(sorted({f.pattern for f in pii}))}); remove them")
