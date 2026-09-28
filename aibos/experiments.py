"""Experiment tracking (Part 20).

Every experiment records HYPOTHESIS, METHOD, METRIC, RESULT, INTERPRETATION,
NEXT ACTION, plus pre-registered success/failure criteria. Results come only
from supplied data; `evaluate_ab` does the statistics.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from aibos import paths
from aibos.schemas import Experiment, stable_hash, to_jsonable
from aibos.store import JsonlStore

EXPERIMENT_TYPES = ("content", "product", "pricing", "landing_page", "audience", "distribution",
                    "offer", "ab_test", "validation")
REQUIRED = ("hypothesis", "method", "metric", "success_criteria", "failure_criteria")


class ExperimentError(ValueError):
    pass


def validate(d: dict[str, Any]) -> list[str]:
    problems = [f"missing {k.upper()}" for k in REQUIRED if not str(d.get(k, "")).strip()]
    if d.get("experiment_type") and d["experiment_type"] not in EXPERIMENT_TYPES:
        problems.append(f"unknown experiment_type {d['experiment_type']!r}")
    hyp = str(d.get("hypothesis", "")).lower()
    if hyp and not any(w in hyp for w in ("if ", "will ", "at least", "more than", "fewer", "increase", "decrease", "%")):
        problems.append("HYPOTHESIS is not clearly falsifiable (state an expected, measurable change)")
    return problems


def from_dict(d: dict[str, Any]) -> Experiment:
    d = dict(d)
    d.setdefault("experiment_id", "exp_" + stable_hash(d.get("name"), d.get("hypothesis")))
    d.setdefault("name", d.get("hypothesis", "")[:60])
    d.setdefault("experiment_type", "validation")
    d.setdefault("created_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    allowed = set(Experiment.__dataclass_fields__)
    return Experiment(**{k: v for k, v in d.items() if k in allowed})


class ExperimentStore:
    def __init__(self) -> None:
        self.store = JsonlStore(paths.sub("experiments") / "experiments.jsonl")

    def register(self, d: dict[str, Any]) -> Experiment:
        problems = validate(d)
        if problems:
            raise ExperimentError("; ".join(problems))
        exp = from_dict(d)
        existing = {e["experiment_id"] for e in self.store}
        if exp.experiment_id not in existing:
            self.store.append(exp)
        return exp

    def all(self) -> list[dict[str, Any]]:
        return self.store.all()

    def record_result(self, experiment_id: str, result: str, interpretation: str, next_action: str,
                      data: dict[str, Any] | None = None) -> dict[str, Any]:
        items = self.store.all()
        for e in items:
            if e["experiment_id"] == experiment_id:
                e.update(result=result, interpretation=interpretation, next_action=next_action,
                         status="COMPLETED", data={**e.get("data", {}), **(data or {})})
                self.store.rewrite(items)
                return e
        raise KeyError(experiment_id)


def sample_size_per_variant(baseline: float, mde_abs: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Two-proportion sample size (normal approximation)."""
    if not (0 < baseline < 1) or mde_abs <= 0:
        raise ValueError("baseline must be in (0,1) and mde_abs > 0")
    z_a = _z(1 - alpha / 2)
    z_b = _z(power)
    p1, p2 = baseline, min(0.999, baseline + mde_abs)
    pbar = (p1 + p2) / 2
    n = ((z_a * math.sqrt(2 * pbar * (1 - pbar)) + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (mde_abs ** 2)
    return int(math.ceil(n))


def evaluate_ab(conv_a: int, n_a: int, conv_b: int, n_b: int, alpha: float = 0.05) -> dict[str, Any]:
    if min(n_a, n_b) <= 0:
        return {"status": "NO DATA", "detail": "sample sizes must be > 0"}
    pa, pb = conv_a / n_a, conv_b / n_b
    p = (conv_a + conv_b) / (n_a + n_b)
    se = math.sqrt(p * (1 - p) * (1 / n_a + 1 / n_b))
    z = (pb - pa) / se if se > 0 else 0.0
    pval = 2 * (1 - _phi(abs(z)))
    return {
        "rate_a": round(pa, 5), "rate_b": round(pb, 5), "abs_lift": round(pb - pa, 5),
        "rel_lift": round((pb - pa) / pa, 4) if pa else None, "z": round(z, 4), "p_value": round(pval, 5),
        "significant": pval < alpha,
        "interpretation": ("B differs from A at the chosen significance level" if pval < alpha
                           else "No statistically significant difference; do not claim a winner"),
    }


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _z(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if _phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def as_record(exp: Experiment) -> dict[str, Any]:
    d = to_jsonable(exp)
    return {"HYPOTHESIS": d["hypothesis"], "METHOD": d["method"], "METRIC": d["metric"],
            "RESULT": d["result"], "INTERPRETATION": d["interpretation"] or "(pending)",
            "NEXT ACTION": d["next_action"] or "(pending)", "SUCCESS CRITERIA": d["success_criteria"],
            "FAILURE CRITERIA": d["failure_criteria"], "STATUS": d["status"]}
