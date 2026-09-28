"""Prompt assembly: shared contract + family template + agent focus + context."""
from __future__ import annotations

import json
from typing import Any

from aibos import config
from aibos.paths import PROMPTS_DIR
from aibos.schemas import AgentSpec

MAX_CONTEXT_CHARS = 60_000


def _read(name: str) -> str:
    p = PROMPTS_DIR / f"{name}.md"
    return p.read_text() if p.exists() else ""


def render(template: str, variables: dict[str, Any]) -> str:
    for k, v in variables.items():
        template = template.replace("{{" + k + "}}", str(v))
    return template


def build(spec: AgentSpec, task: str, context: dict[str, Any], today: str) -> tuple[str, str]:
    platform = {}
    if spec.params.get("platform"):
        platform = config.platforms().get(spec.params["platform"], {})
    variables = {
        "agent_name": spec.name, "agent_id": spec.agent_id, "purpose": spec.purpose,
        "focus": spec.focus, "domain": spec.domain, "today": today,
        "outputs": ", ".join(spec.outputs),
        "restricted": ", ".join(spec.restricted_actions),
        "confidence": json.dumps(spec.confidence_requirements),
        "platform_rules": json.dumps(platform, indent=2) if platform else "n/a",
        "params": json.dumps(spec.params),
        "brand_voice": json.dumps(config.brand(), indent=2),
    }
    system = render(_read("_contract"), variables) + "\n\n" + render(_read(spec.prompt_template) or _read("default"), variables)
    ctx = json.dumps(context, indent=1, default=str, ensure_ascii=False)
    if len(ctx) > MAX_CONTEXT_CHARS:
        # Do not silently truncate: tell the agent the context was cut.
        ctx = ctx[:MAX_CONTEXT_CHARS] + "\n... [CONTEXT TRUNCATED — state this as an uncertainty]"
    user = f"TASK:\n{task}\n\nCONTEXT (JSON):\n{ctx}\n\nReturn ONLY the JSON object described in the contract."
    return system, user
