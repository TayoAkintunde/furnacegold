"""Model backends for LLM agents.

- OfflineBackend:   no model available. Returns NO_MODEL honestly and saves the
                    prompt so an operator can see exactly what would be asked.
- ScriptedBackend:  responses supplied from a JSON file (tests, demos, or an
                    operator/another assistant answering prompts out-of-band).
                    Provenance is recorded on every output.
- AnthropicBackend: Claude via the official `anthropic` SDK. Requires the SDK
                    and credentials; otherwise reports CREDENTIAL REQUIRED.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aibos import config, cost, integrations
from aibos.schemas import AgentSpec, RunStatus


@dataclass
class BackendResult:
    status: RunStatus
    payload: dict[str, Any] = field(default_factory=dict)
    provenance: str = ""
    usd: float = 0.0
    error: str = ""
    cacheable: bool = False


class Backend:
    name = "base"

    def complete(self, spec: AgentSpec, system: str, user: str) -> BackendResult:  # pragma: no cover
        raise NotImplementedError


class OfflineBackend(Backend):
    name = "offline"

    def complete(self, spec: AgentSpec, system: str, user: str) -> BackendResult:
        st = integrations.status("anthropic")
        return BackendResult(
            RunStatus.NO_MODEL,
            provenance="offline: no model call made",
            error=f"No model backend connected (anthropic: {st.status} — {st.detail}). "
                  "Prompt saved; no output was generated.")


class ScriptedBackend(Backend):
    name = "scripted"

    def __init__(self, responses: dict[str, Any], provenance: str = "scripted responses"):
        self.responses = responses
        self.provenance = provenance
        self.used: list[str] = []

    @classmethod
    def from_file(cls, path: str | Path) -> "ScriptedBackend":
        raw = json.loads(Path(path).read_text())
        return cls(raw.get("responses", raw), raw.get("provenance", f"scripted from {Path(path).name}"))

    def complete(self, spec: AgentSpec, system: str, user: str) -> BackendResult:
        resp = self.responses.get(spec.agent_id)
        if resp is None:
            return BackendResult(RunStatus.NO_MODEL, provenance=self.provenance,
                                 error=f"no scripted response for {spec.agent_id}")
        self.used.append(spec.agent_id)
        return BackendResult(RunStatus.OK, payload=resp, provenance=self.provenance)


class AnthropicBackend(Backend):
    name = "anthropic"

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic  # optional dependency
            self._client = anthropic.Anthropic()
        return self._client

    def complete(self, spec: AgentSpec, system: str, user: str) -> BackendResult:
        st = integrations.status("anthropic")
        if st.status != integrations.CONNECTED:
            code = RunStatus.CREDENTIAL_REQUIRED if st.status == integrations.CREDENTIAL_REQUIRED else RunStatus.NOT_CONNECTED
            return BackendResult(code, error=f"anthropic: {st.status} ({st.detail})")
        import anthropic
        mcfg = cost.model_for(spec.cost_class)
        model = mcfg.get("model", "claude-opus-5")
        kwargs: dict[str, Any] = dict(model=model, max_tokens=int(mcfg.get("max_tokens", 8000)),
                                      system=system, messages=[{"role": "user", "content": user}])
        if mcfg.get("effort"):
            kwargs["output_config"] = {"effort": mcfg["effort"]}
        if model.startswith("claude-opus-5") and config.settings().get("server_side_fallbacks", True):
            kwargs["extra_headers"] = {"anthropic-beta": "server-side-fallback-2026-07-01"}
            kwargs["extra_body"] = {"fallbacks": "default"}
        try:
            resp = self._get_client().messages.create(**kwargs)
        except anthropic.RateLimitError as exc:
            return BackendResult(RunStatus.FAILED, error=f"rate limited: {exc}")
        except anthropic.APIStatusError as exc:
            return BackendResult(RunStatus.FAILED, error=f"API error {exc.status_code}: {exc.message}")
        except anthropic.APIConnectionError as exc:
            return BackendResult(RunStatus.NOT_CONNECTED, error=f"connection error: {exc}")
        usd = cost.usd_for(model, resp.usage.input_tokens, resp.usage.output_tokens)
        if resp.stop_reason == "refusal":
            return BackendResult(RunStatus.FAILED, usd=usd, provenance=f"anthropic:{model}",
                                 error="model declined the request (stop_reason=refusal)")
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        try:
            payload = parse_json_object(text)
        except ValueError as exc:
            return BackendResult(RunStatus.FAILED, usd=usd, provenance=f"anthropic:{model}",
                                 error=f"unparseable output: {exc}")
        return BackendResult(RunStatus.OK, payload=payload, provenance=f"anthropic:{model}",
                             usd=usd, cacheable=True)


def parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if m:
        text = m.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object found")
    return json.loads(text[start:end + 1])


def get_backend(name: str = "auto", responses: str | None = None) -> Backend:
    if responses:
        return ScriptedBackend.from_file(responses)
    if name == "anthropic":
        return AnthropicBackend()
    if name == "offline":
        return OfflineBackend()
    return AnthropicBackend() if integrations.is_connected("anthropic") else OfflineBackend()
