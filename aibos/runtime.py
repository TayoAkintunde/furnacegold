"""Agent runtime: executes one agent against the run context."""
from __future__ import annotations

import json
import time
import traceback

from aibos import prompts, security
from aibos.backends import Backend
from aibos.cost import BudgetExceeded, ResponseCache, units_for
from aibos.rules import RULES
from aibos.schemas import (STRUCTURED_OUTPUT_KEYS, AgentOutput, AgentSpec, AgentStatus, RunStatus,
                           stable_hash)
from aibos.store import write_json


def _normalize_payload(spec: AgentSpec, task: str, payload: dict) -> AgentOutput:
    p = {str(k).upper(): v for k, v in payload.items()}
    o = AgentOutput(agent_id=spec.agent_id, task=str(p.get("TASK", task)))
    for key in ("FINDINGS", "EVIDENCE", "ASSUMPTIONS", "UNCERTAINTIES", "RECOMMENDATIONS", "SOURCES",
                "FILES_CHANGED", "TESTS_PERFORMED"):
        v = p.get(key, [])
        setattr(o, key.lower(), v if isinstance(v, list) else [v])
    o.next_action = str(p.get("NEXT_ACTION", ""))
    o.data = p.get("DATA", {}) if isinstance(p.get("DATA", {}), dict) else {}
    try:
        o.confidence = float(p.get("CONFIDENCE", 0.0))
    except (TypeError, ValueError):
        o.confidence = 0.0
    missing = [k for k in STRUCTURED_OUTPUT_KEYS if k not in p]
    if missing:
        o.errors.append(f"output contract violation: missing {missing}")
        o.status = RunStatus.DEGRADED
    return o


class AgentRunner:
    def __init__(self, backend: Backend):
        self.backend = backend
        self.cache = ResponseCache()

    def run(self, spec: AgentSpec, ctx, task: str) -> AgentOutput:
        t0 = time.perf_counter()
        o = self._dispatch(spec, ctx, task)
        o.duration_s = time.perf_counter() - t0
        if o.status in (RunStatus.OK, RunStatus.DEGRADED):
            self._merge(spec, ctx, o)
        min_conf = float(spec.confidence_requirements.get("min_confidence", 0.0) or 0.0)
        if o.status == RunStatus.OK and not spec.is_rule and o.confidence < min_conf:
            msg = f"{spec.agent_id} confidence {o.confidence} below required {min_conf}"
            o.uncertainties.append(msg)
            ctx.escalations.append(msg + " — treat its output as low-confidence")
        ctx.outputs.append(o)
        ctx.perf.record(run_id=ctx.run_id, agent_id=spec.agent_id, task=task, status=o.status.value,
                        duration_s=o.duration_s, cost_units=o.cost_units,
                        quality=o.confidence if o.status == RunStatus.OK else None, errors=o.errors,
                        backend=o.backend, output_summary="; ".join(map(str, o.findings[:3])))
        if ctx.persist:
            write_json(ctx.run_dir / "agents" / f"{spec.agent_id}.json", o.to_dict())
        return o

    # ------------------------------------------------------------------
    def _dispatch(self, spec: AgentSpec, ctx, task: str) -> AgentOutput:
        if spec.status in (AgentStatus.DISABLED, AgentStatus.DEPRECATED):
            return AgentOutput(spec.agent_id, task, RunStatus.SKIPPED, errors=[f"agent is {spec.status.value}"])
        try:
            ctx.budget.check(spec)
        except BudgetExceeded as exc:
            ctx.escalations.append(str(exc))
            return AgentOutput(spec.agent_id, task, RunStatus.SKIPPED, errors=[str(exc)])
        if spec.is_rule:
            fn = RULES.get(spec.rule_name)
            if fn is None:
                return AgentOutput(spec.agent_id, task, RunStatus.FAILED, errors=[f"rule {spec.rule_name} not implemented"])
            try:
                o = fn(ctx, spec)
            except Exception as exc:  # a failing rule must be reported, not hidden
                return AgentOutput(spec.agent_id, task, RunStatus.FAILED, backend="rule",
                                   errors=[f"{type(exc).__name__}: {exc}", traceback.format_exc(limit=3)])
            ctx.budget.charge(spec, units_for(spec))
            o.task = task
            return o
        if spec.executor == "llm":
            return self._llm(spec, ctx, task)
        return AgentOutput(spec.agent_id, task, RunStatus.SKIPPED, errors=[f"executor {spec.executor} is not directly runnable"])

    def _llm(self, spec: AgentSpec, ctx, task: str) -> AgentOutput:
        keys = list(dict.fromkeys(spec.required_context + spec.inputs))
        system, user = prompts.build(spec, task, ctx.context_for(keys), ctx.today)
        if ctx.persist:
            p = ctx.run_dir / "prompts" / f"{spec.agent_id}.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"# SYSTEM\n\n{system}\n\n# USER\n\n{user}\n")
        key = stable_hash(spec.agent_id, spec.prompt_version, self.backend.name, system, user)
        cached = self.cache.get(key) if self.backend.name == "anthropic" else None
        if cached is not None:
            o = _normalize_payload(spec, task, cached["payload"])
            o.backend, o.provenance = self.backend.name, cached["provenance"] + " (cache hit)"
            return o
        res = self.backend.complete(spec, system, user)
        if res.status != RunStatus.OK:
            return AgentOutput(spec.agent_id, task, res.status, backend=self.backend.name,
                               provenance=res.provenance, errors=[res.error] if res.error else [])
        leaked = security.scan_secrets(json.dumps(res.payload, default=str))
        if leaked:
            ctx.escalations.append(f"{spec.agent_id} output contained secret-like values; output blocked")
            return AgentOutput(spec.agent_id, task, RunStatus.BLOCKED, backend=self.backend.name,
                               errors=[f"secret detected: {leaked[0].pattern}"])
        units = units_for(spec)
        ctx.budget.charge(spec, units, res.usd, llm_call=self.backend.name == "anthropic")
        if res.cacheable:
            self.cache.put(key, {"payload": res.payload, "provenance": res.provenance})
        o = _normalize_payload(spec, task, res.payload)
        o.backend, o.provenance, o.cost_units = self.backend.name, res.provenance, units
        return o

    @staticmethod
    def _merge(spec: AgentSpec, ctx, o: AgentOutput) -> None:
        for key, value in (o.data or {}).items():
            if spec.is_rule or key in spec.outputs:
                ctx.merge(key, value, spec.agent_id)
            else:
                o.errors.append(f"ignored undeclared output '{key}' (not in registry outputs)")
