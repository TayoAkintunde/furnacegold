"""Cost control (Part 29): cost classes, per-run budget, and a response cache so
identical work is not repeated."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from aibos import config, paths
from aibos.schemas import AgentSpec, CostClass
from aibos.store import read_json, write_json


class BudgetExceeded(RuntimeError):
    pass


def units_for(spec: AgentSpec) -> float:
    table = config.settings().get("cost_units", {})
    if spec.is_rule or spec.executor == "orchestrator":
        return float(table.get("RULE", 0))
    return float(table.get(spec.cost_class.value, 1))


def model_for(cost_class: CostClass) -> dict[str, Any]:
    return dict(config.settings().get("models", {}).get(cost_class.value, {}))


def usd_for(model: str, input_tokens: int, output_tokens: int) -> float:
    price = config.settings().get("pricing_per_mtok", {}).get(model)
    if not price:
        return 0.0
    return round(input_tokens / 1e6 * price[0] + output_tokens / 1e6 * price[1], 6)


@dataclass
class Budget:
    max_units: float
    max_llm_calls: int
    spent_units: float = 0.0
    llm_calls: int = 0
    usd: float = 0.0
    ledger: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_settings(cls) -> "Budget":
        b = config.settings().get("budget", {})
        return cls(float(b.get("max_cost_units_per_run", 400)), int(b.get("max_llm_calls_per_run", 30)))

    def check(self, spec: AgentSpec) -> None:
        u = units_for(spec)
        if self.spent_units + u > self.max_units:
            raise BudgetExceeded(f"{spec.agent_id} would exceed run budget ({self.spent_units}+{u}>{self.max_units})")
        if not spec.is_rule and spec.executor == "llm" and self.llm_calls + 1 > self.max_llm_calls:
            raise BudgetExceeded(f"LLM call limit {self.max_llm_calls} reached")

    def charge(self, spec: AgentSpec, units: float, usd: float = 0.0, llm_call: bool = False) -> None:
        self.spent_units += units
        self.usd += usd
        self.llm_calls += int(llm_call)
        self.ledger.append({"agent_id": spec.agent_id, "units": units, "usd": usd, "llm_call": llm_call})


class ResponseCache:
    """Caches model outputs keyed by (agent, prompt version, prompt hash)."""

    def __init__(self) -> None:
        s = config.settings().get("cache", {})
        self.enabled = bool(s.get("enabled", True))
        self.ttl = float(s.get("ttl_hours", 72)) * 3600
        self.dir = paths.sub("cache")

    def get(self, key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        rec = read_json(self.dir / f"{key}.json")
        if not rec or time.time() - rec.get("ts", 0) > self.ttl:
            return None
        return rec["value"]

    def put(self, key: str, value: dict[str, Any]) -> None:
        if self.enabled:
            write_json(self.dir / f"{key}.json", {"ts": time.time(), "value": value})
