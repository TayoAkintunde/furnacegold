"""Core data contracts shared by every part of the AI Business OS.

Everything that moves between agents is a dataclass defined here, so that
agent communication is structured (Part 26) and evidence is explicit (Part 27).
"""
from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


class AgentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPERIMENTAL = "EXPERIMENTAL"
    DEPRECATED = "DEPRECATED"
    DISABLED = "DISABLED"


class CostClass(str, enum.Enum):
    LOW_COST = "LOW_COST"
    MEDIUM_COST = "MEDIUM_COST"
    HIGH_COST = "HIGH_COST"


class Level(int, enum.Enum):
    MASTER = 0
    DOMAIN_ORCHESTRATOR = 1
    SPECIALIST = 2
    MICRO_SPECIALIST = 3
    QUALITY = 4
    ANALYTICS_LEARNING = 5


class RunStatus(str, enum.Enum):
    """Outcome of one agent invocation. Never report OK for something that did not happen."""
    OK = "OK"
    DEGRADED = "DEGRADED"                  # ran, but with reduced capability (e.g. no model)
    NO_MODEL = "NO_MODEL"                  # LLM agent, no model backend available
    NOT_CONNECTED = "NOT_CONNECTED"        # a required integration is not connected
    CREDENTIAL_REQUIRED = "CREDENTIAL_REQUIRED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    BLOCKED = "BLOCKED"                    # blocked by security / permission policy
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ClaimKind(str, enum.Enum):
    FACT = "FACT"                  # verified against evidence
    OBSERVATION = "OBSERVATION"    # directly observed in supplied data
    ASSUMPTION = "ASSUMPTION"
    HYPOTHESIS = "HYPOTHESIS"
    OPINION = "OPINION"


class Verification(str, enum.Enum):
    UNVERIFIED = "UNVERIFIED"
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNSUPPORTED = "UNSUPPORTED"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


REQUIRED_AGENT_FIELDS = (
    "agent_id", "name", "domain", "purpose", "inputs", "outputs", "tools",
    "dependencies", "required_context", "allowed_actions", "restricted_actions",
    "confidence_requirements", "quality_checks", "escalation_rules",
    "cost_class", "priority", "status",
)


@dataclass
class AgentSpec:
    """A registry entry. Behaviour comes from `executor` + prompt template, not bespoke code."""
    agent_id: str
    name: str
    domain: str
    purpose: str
    inputs: list[str]
    outputs: list[str]
    tools: list[str]
    dependencies: list[str]
    required_context: list[str]
    allowed_actions: list[str]
    restricted_actions: list[str]
    confidence_requirements: dict[str, Any]
    quality_checks: list[str]
    escalation_rules: list[str]
    cost_class: CostClass
    priority: int
    status: AgentStatus
    # Extension fields (not required by the contract, but used by the runtime)
    level: Level = Level.SPECIALIST
    family: str = ""
    executor: str = "llm"               # "llm" or "rule:<name>"
    prompt_template: str = "default"
    focus: str = ""                     # domain-specific focus injected into the template
    keywords: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    critical: bool = False              # critical instructions: never auto-modified
    prompt_version: str = "1.0"
    last_reviewed: str = ""
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def is_rule(self) -> bool:
        return self.executor.startswith("rule:")

    @property
    def rule_name(self) -> str:
        return self.executor.split(":", 1)[1] if self.is_rule else ""

    def to_dict(self) -> dict[str, Any]:
        return to_jsonable(self)


@dataclass
class Source:
    """A captured source. `text` is the verbatim captured content; never synthesised."""
    source_id: str
    url: str
    title: str
    publisher: str
    source_type: str          # primary | official_docs | paper | repository | news | blog | social | unknown
    published: str = ""       # ISO date as stated by the source ("" if unknown)
    retrieved_at: str = ""
    retrieved_by: str = ""    # which tool/person captured it
    text: str = ""
    notes: str = ""


@dataclass
class Claim:
    claim_id: str
    text: str
    kind: ClaimKind = ClaimKind.ASSUMPTION
    source_ids: list[str] = field(default_factory=list)
    quotes: list[str] = field(default_factory=list)   # verbatim supporting excerpts
    confidence: float = 0.0
    verification: Verification = Verification.UNVERIFIED
    verification_notes: list[str] = field(default_factory=list)


@dataclass
class EvidenceLink:
    """CLAIM -> SOURCE -> EVIDENCE -> CONFIDENCE -> INTERPRETATION -> DECISION (Part 27)."""
    claim: str
    source: str
    evidence: str
    confidence: float
    interpretation: str
    decision: str


@dataclass
class AgentOutput:
    """The structured message every agent returns (Part 26)."""
    agent_id: str
    task: str
    status: RunStatus = RunStatus.OK
    findings: list[Any] = field(default_factory=list)
    evidence: list[Any] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    next_action: str = ""
    sources: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    files_changed: list[str] = field(default_factory=list)
    tests_performed: list[str] = field(default_factory=list)
    confidence: float = 0.0
    backend: str = ""
    provenance: str = ""
    cost_units: float = 0.0
    duration_s: float = 0.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return to_jsonable(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AgentOutput":
        names = {f.name for f in dataclasses.fields(cls)}
        kwargs = {k.lower(): v for k, v in d.items() if k.lower() in names}
        if "status" in kwargs:
            kwargs["status"] = RunStatus(kwargs["status"])
        return cls(**kwargs)


STRUCTURED_OUTPUT_KEYS = ("TASK", "FINDINGS", "EVIDENCE", "ASSUMPTIONS", "UNCERTAINTIES",
                          "RECOMMENDATIONS", "NEXT_ACTION")


@dataclass
class TaskProfile:
    """Part 25: the dimensions used to select agents."""
    objective: str
    task_type: str
    domains: list[str]
    required_expertise: list[str]
    required_tools: list[str]
    risk_level: RiskLevel
    complexity: str           # simple | medium | complex
    output_type: str
    stages: list[str]
    keywords: list[str]


@dataclass
class Experiment:
    """Part 20: every experiment records these fields."""
    experiment_id: str
    name: str
    experiment_type: str
    hypothesis: str
    method: str
    metric: str
    success_criteria: str
    failure_criteria: str
    result: str = "NOT RUN"
    interpretation: str = ""
    next_action: str = ""
    status: str = "DESIGNED"   # DESIGNED | APPROVED | RUNNING | COMPLETED | ABANDONED
    variants: list[str] = field(default_factory=list)
    min_sample_per_variant: int = 0
    created_at: str = ""
    data: dict[str, Any] = field(default_factory=dict)


def to_jsonable(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_jsonable(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    return obj


def stable_hash(*parts: Any) -> str:
    payload = json.dumps(to_jsonable(list(parts)), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]
