"""Security primitives (Part 22): secret/credential/PII detection, redaction,
prompt-injection detection, permission checks and tool-risk ratings."""
from __future__ import annotations

import re
from dataclasses import dataclass

from aibos import config
from aibos.schemas import AgentSpec

SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "anthropic_key": re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    "openai_style_key": re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "slack_token": re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),
    "bearer_token": re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_\-\.=]{24,}"),
}
CREDENTIAL_PATTERNS: dict[str, re.Pattern[str]] = {
    "password_assignment": re.compile(r"(?i)\b(pass(word|wd)?|pwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?[^\s'\"]{6,}"),
    "connection_string": re.compile(r"(?i)\b(postgres(ql)?|mysql|mongodb(\+srv)?|redis|amqp)://[^\s:@]+:[^\s@]+@"),
}
PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?<!\w)\+?\d[\d\s().\-]{8,}\d(?!\w)"),
    "card_number": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
}
INJECTION_PATTERNS: list[re.Pattern[str]] = [re.compile(p, re.I) for p in (
    r"ignore (all |any )?(previous|prior|above) (instructions|prompts|directions)",
    r"disregard (the |all |your )?(previous|prior|above|system) (instructions|prompt)",
    r"you are now (a|an|the) ",
    r"new (system )?instructions?:",
    r"system prompt",
    r"(reveal|print|output|show) (your|the) (system prompt|instructions|api key|secrets?)",
    r"do not (tell|inform) the (user|operator)",
    r"(send|post|upload|exfiltrate) .{0,40}(to|at) https?://",
    r"<\s*/?\s*(system|assistant|instructions?)\s*>",
    r"act as (if you are|an?) (?:unfiltered|jailbroken|dan)",
)]

# Actions that can have external effects, and the approval category each maps to.
EXTERNAL_ACTION_CATEGORIES = {
    "publish": "publish_content",
    "send_external_message": "send_external_message",
    "spend_money": "financial_transaction",
    "process_payment": "financial_transaction",
    "run_paid_ads": "paid_advertising",
    "launch_product": "major_product_launch",
    "sign_contract": "external_contract",
    "commit_to_client": "external_contract",
    "delete_data": "delete_important_data",
    "deploy_production": "production_change",
    "change_infrastructure": "production_change",
    "set_live_prices": "financial_transaction",
}
TOOL_RISK = {
    "source_store": "LOW", "memory_store": "LOW", "metrics_store": "LOW", "registry": "LOW",
    "selector": "LOW", "blackboard": "LOW", "platform_rules": "LOW", "experiment_store": "LOW",
    "performance_store": "LOW", "repository_read": "LOW",
    "web_search": "MEDIUM", "http_fetch": "MEDIUM", "arxiv": "LOW", "github": "MEDIUM",
    "scheduler": "MEDIUM",
}


@dataclass
class Finding:
    kind: str
    pattern: str
    location: str
    excerpt: str
    severity: str = "HIGH"


def _mask(s: str) -> str:
    s = s.strip()
    return (s[:4] + "…" + s[-2:]) if len(s) > 8 else "…"


def scan_secrets(text: str, location: str = "", credentials: bool = True) -> list[Finding]:
    out: list[Finding] = []
    pats = dict(SECRET_PATTERNS)
    if credentials:
        pats.update(CREDENTIAL_PATTERNS)
    for name, pat in pats.items():
        for m in pat.finditer(text or ""):
            out.append(Finding("secret", name, location, _mask(m.group(0)), "CRITICAL"))
    return out


def scan_pii(text: str, location: str = "") -> list[Finding]:
    out = []
    for name, pat in PII_PATTERNS.items():
        for m in pat.finditer(text or ""):
            val = m.group(0)
            if name == "phone" and sum(c.isdigit() for c in val) < 10:
                continue
            if name == "card_number" and not _luhn(val):
                continue
            out.append(Finding("pii", name, location, _mask(val), "MEDIUM"))
    return out


def _luhn(s: str) -> bool:
    digits = [int(c) for c in s if c.isdigit()]
    if len(digits) < 13:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2:
            d *= 2
            d -= 9 if d > 9 else 0
        total += d
    return total % 10 == 0


def scan_injection(text: str, location: str = "") -> list[Finding]:
    out = []
    for pat in INJECTION_PATTERNS:
        for m in pat.finditer(text or ""):
            out.append(Finding("prompt_injection", pat.pattern, location, m.group(0)[:80], "HIGH"))
    return out


def redact(text: str) -> str:
    """Redact secrets, credentials and PII before anything is persisted."""
    for pat in list(SECRET_PATTERNS.values()) + list(CREDENTIAL_PATTERNS.values()):
        text = pat.sub("[REDACTED-SECRET]", text)
    text = PII_PATTERNS["email"].sub("[REDACTED-EMAIL]", text)
    return text


def approval_categories() -> set[str]:
    return set(config.settings().get("approval_required", []))


def requires_approval(category: str) -> bool:
    return category in approval_categories()


def check_action(spec: AgentSpec, action: str) -> tuple[bool, str]:
    """Permission check for an agent attempting an action.

    Returns (allowed, reason). External actions are never executed directly —
    they are allowed only as *queued* approval requests.
    """
    if action in spec.restricted_actions:
        return False, f"{action} is restricted for {spec.agent_id}"
    category = EXTERNAL_ACTION_CATEGORIES.get(action)
    if category and requires_approval(category):
        return False, f"{action} requires human approval ({category}); queue it instead"
    if action not in spec.allowed_actions:
        return False, f"{action} is not in allowed_actions of {spec.agent_id}"
    return True, "allowed"


def tool_risk(tool: str) -> str:
    return TOOL_RISK.get(tool, "UNKNOWN")
