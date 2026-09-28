"""Central agent registry (Part 3).

Agents are declared in YAML family files under agents/registry/. A family file
declares `defaults` (a template shared by every agent in the family) and a
compact `agents` list with per-agent overrides. Agents that behave identically
except for their domain differ only in `focus`/`keywords`/`params`, so hundreds
of specialists stay maintainable without duplicated code.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Iterable

import yaml

from aibos.paths import REGISTRY_DIR
from aibos.schemas import (REQUIRED_AGENT_FIELDS, AgentSpec, AgentStatus, CostClass,
                           Level)


class RegistryError(ValueError):
    pass


_LIST_FIELDS = {"inputs", "outputs", "tools", "dependencies", "required_context",
                "allowed_actions", "restricted_actions", "quality_checks",
                "escalation_rules", "keywords", "capabilities"}


def _fmt(value: Any, variables: dict[str, str]) -> Any:
    if isinstance(value, str):
        try:
            return value.format(**variables)
        except (KeyError, IndexError):
            return value
    if isinstance(value, list):
        return [_fmt(v, variables) for v in value]
    if isinstance(value, dict):
        return {k: _fmt(v, variables) for k, v in value.items()}
    return value


def expand_family(doc: dict[str, Any], source: str = "") -> list[AgentSpec]:
    family = doc["family"]
    defaults = doc.get("defaults", {}) or {}
    specs: list[AgentSpec] = []
    for entry in doc.get("agents", []) or []:
        raw = copy.deepcopy(defaults)
        entry = dict(entry)
        short_id = entry.pop("id")
        # `extra_<field>` appends to a list field instead of replacing it.
        for key in list(entry):
            if key.startswith("extra_"):
                base = key[len("extra_"):]
                raw[base] = list(raw.get(base, [])) + list(entry.pop(key))
        raw.update(entry)
        raw.setdefault("domain", doc.get("domain", family))
        raw["agent_id"] = entry.get("agent_id", f"{family}.{short_id}")
        raw["family"] = family
        raw.setdefault("level", doc.get("level", 2))
        variables = {"name": raw.get("name", short_id), "focus": raw.get("focus", ""),
                     "domain": raw["domain"]}
        raw = _fmt(raw, variables)
        specs.append(_build(raw, source))
    return specs


def _build(raw: dict[str, Any], source: str) -> AgentSpec:
    missing = [f for f in REQUIRED_AGENT_FIELDS if f not in raw]
    if missing:
        raise RegistryError(f"{source}: agent {raw.get('agent_id')} missing fields {missing}")
    for f in _LIST_FIELDS:
        if f in raw and not isinstance(raw[f], list):
            raise RegistryError(f"{source}: {raw['agent_id']}.{f} must be a list")
    try:
        raw["cost_class"] = CostClass(raw["cost_class"])
        raw["status"] = AgentStatus(raw["status"])
        raw["level"] = Level(int(raw["level"]))
    except ValueError as exc:
        raise RegistryError(f"{source}: {raw['agent_id']}: {exc}") from exc
    if not isinstance(raw["confidence_requirements"], dict):
        raise RegistryError(f"{source}: {raw['agent_id']}.confidence_requirements must be a mapping")
    known = {f for f in AgentSpec.__dataclass_fields__}
    unknown = set(raw) - known
    if unknown:
        raise RegistryError(f"{source}: {raw['agent_id']} has unknown fields {sorted(unknown)}")
    return AgentSpec(**raw)


class Registry:
    def __init__(self, specs: Iterable[AgentSpec], families: dict[str, dict] | None = None):
        self._agents: dict[str, AgentSpec] = {}
        for s in specs:
            if s.agent_id in self._agents:
                raise RegistryError(f"duplicate agent_id {s.agent_id}")
            self._agents[s.agent_id] = s
        self.families = families or {}
        self._validate_dependencies()

    @classmethod
    def load(cls, directory: Path | None = None) -> "Registry":
        directory = Path(directory or REGISTRY_DIR)
        specs: list[AgentSpec] = []
        families: dict[str, dict] = {}
        files = sorted(directory.glob("*.yaml"))
        if not files:
            raise RegistryError(f"no registry files in {directory}")
        for path in files:
            doc = yaml.safe_load(path.read_text())
            if not doc or "family" not in doc:
                raise RegistryError(f"{path.name}: missing 'family'")
            families[doc["family"]] = {k: v for k, v in doc.items() if k not in ("agents", "defaults")}
            specs.extend(expand_family(doc, path.name))
        return cls(specs, families)

    def _validate_dependencies(self) -> None:
        for s in self._agents.values():
            for dep in s.dependencies:
                if dep not in self._agents:
                    raise RegistryError(f"{s.agent_id} depends on unknown agent {dep}")
            for qc in s.quality_checks:
                if qc not in self._agents:
                    raise RegistryError(f"{s.agent_id} quality_check {qc} is not a registered agent")

    # --- queries -------------------------------------------------------
    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def get(self, agent_id: str) -> AgentSpec:
        try:
            return self._agents[agent_id]
        except KeyError:
            raise RegistryError(f"unknown agent {agent_id}") from None

    def all(self) -> list[AgentSpec]:
        return list(self._agents.values())

    def usable(self) -> list[AgentSpec]:
        """Agents the orchestrator may select (ACTIVE or EXPERIMENTAL)."""
        return [a for a in self._agents.values()
                if a.status in (AgentStatus.ACTIVE, AgentStatus.EXPERIMENTAL)]

    def by_family(self, family: str) -> list[AgentSpec]:
        return [a for a in self._agents.values() if a.family == family]

    def by_domain(self, domain: str) -> list[AgentSpec]:
        return [a for a in self._agents.values() if a.domain == domain]

    def by_level(self, level: Level) -> list[AgentSpec]:
        return [a for a in self._agents.values() if a.level == level]

    def with_capability(self, capability: str) -> list[AgentSpec]:
        return [a for a in self.usable() if capability in a.capabilities]

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for a in self._agents.values():
            out[a.family] = out.get(a.family, 0) + 1
        return dict(sorted(out.items()))
