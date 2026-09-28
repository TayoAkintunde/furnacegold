# Architecture

## Design principles

1. **Registry, not code, defines agents.** 319 agents are declared in 22 YAML family files. Agents that differ only in their domain share one template and differ by `focus`, `keywords` and `params`. Adding a specialist is a one-line YAML change.
2. **Smallest sufficient team.** The master orchestrator never activates the whole library. It profiles the objective, activates only the stages it needs, and picks agents per stage. The demo objective uses 10 model-backed agents plus 28 cheap deterministic checks, out of 319.
3. **Deterministic where possible.** 88 agents are *rule agents*: plain Python, no model call, fully testable. They cover verification, content quality, security, analytics, knowledge housekeeping, and learning. Models are reserved for judgement work such as research synthesis, teaching, writing and strategy.
4. **Evidence before facts.** Claims arrive UNVERIFIED. Verifiers check them against captured source text. A claim becomes a FACT only when every content check passes. Downstream stages see only verified claims, and the drafting stages are skipped when nothing is verified.
5. **No fake autonomy.** Nothing is published, sent, bought or deployed. External actions go to an approval queue. Approving an item records the decision but does not claim execution: no publishing adapter exists, so the item is marked `NOT_EXECUTED`. Missing backends and integrations are reported as `NO_MODEL`, `NOT CONNECTED` or `CREDENTIAL REQUIRED`.

## Hierarchy

```
LEVEL 0  orch.master ─ profiles objective, builds plan, runs stages, verifies, resolves conflicts, escalates, records learning
LEVEL 1  15 domain orchestrators (research, knowledge, content, education, audience, marketing, product,
         revenue, customer, analytics, technology, automation, quality, security, learning)
LEVEL 2  specialists           (research, knowledge, content strategy, education, audience, marketing, …)
LEVEL 3  micro-specialists     (platform writers, digital-product types, platform-fit checker)
LEVEL 4  quality/verification  (15 source verifiers, 16 content-quality checks, 10 security agents, registrar)
LEVEL 5  analytics/learning    (metric analysts, anomaly/trend, evaluator, auditor, improvement proposer)
```

## Components (`aibos/`)

| Module | Responsibility | Spec part |
|---|---|---|
| `schemas.py` | `AgentSpec`, `AgentOutput` (TASK/FINDINGS/EVIDENCE/…), `Claim`, `Source`, `EvidenceLink`, `Experiment`, `TaskProfile` | 3, 26, 27 |
| `registry.py` | Loads and validates `agents/registry/*.yaml`, expands family templates, checks dependencies and quality-check references | 3 |
| `selection.py` | Task profiler (task type, domains, expertise, tools, risk, complexity, output type), stage detection, per-stage agent scoring, team-size caps | 25 |
| `orchestrator.py` | `MasterOrchestrator`, `DomainOrchestrator`, stage hooks (verification aggregation, quality gate, approval queue, distribution status, launch gate, weekly report), evidence guard, evidence-dependency gating | 24 |
| `runtime.py` | Runs one agent: status/budget checks, rule or model dispatch, output-contract validation, secret scan of model output, declared-output merging, confidence escalation, performance logging | 26, 29, 31 |
| `backends.py` | `AnthropicBackend` (official SDK, cost-class → model tier, refusal handling), `OfflineBackend` (honest NO_MODEL), `ScriptedBackend` (recorded responses with provenance) | 29, 43 |
| `prompts.py`, `agents/prompts/` | Shared output contract + 12 family templates | 26 |
| `rules/` | 66 deterministic rule implementations (verification, knowledge, content quality, security, analytics, ops) | 5, 6, 9, 19–22 |
| `evidence.py` | Source store, quote matching, verification aggregation, confidence, evidence chains | 27 |
| `conflict.py` | Conflict detection and resolution. Prefers primary evidence and keeps disagreement when unresolved. | 28 |
| `cost.py` | Cost classes → units/models, per-run budget, response cache with TTL | 29 |
| `memory.py` | 7 memory levels (JSONL), redaction, refuses secrets and personal data, de-duplication | 30 |
| `performance.py` | Per-agent run records, human corrections, evaluation flags | 31 |
| `audit.py`, `improvement.py` | Agent audit and improvement proposals. Proposals are never applied automatically. | 32, 40 |
| `approval.py` | Human approval queue. Execution is never faked. | 42, 43 |
| `integrations.py` | Computed integration status and the `http_fetch` adapter | 43 |
| `experiments.py` | Experiment store, required fields, A/B z-test, sample size | 20 |
| `analytics.py` | CSV metric import, summaries, robust anomalies, trend. Reports NO DATA when nothing is supplied. | 19 |
| `reports.py` | Per-run chain report and weekly strategy report | 38, 45 |
| `cli.py` | Command interface | 39 |

## Data flow of one run

```
objective ──► profile ──► stages (intents + implies + always) ──► agents per stage (fixed or scored pool)
                                                                    │
   captured sources ─► SOURCE_SECURITY (quarantine injections)       ▼
                      RESEARCH (claims: UNVERIFIED) ─► VERIFY (rule verifiers) ─► aggregate + conflicts
                      KNOWLEDGE (only SUPPORTED → global memory; rest → open questions)
                      TEACH / CONTENT_STRATEGY / CONTENT  (skipped if nothing verified)
                      QUALITY (16 rule checks → quality gate; BLOCKING removes drafts from approval)
                      OPPORTUNITY / PRODUCT / REVENUE / EXPERIMENT (+ registrar) / ANALYTICS_PLAN
                      APPROVAL (queue; nothing published) ─► SECURITY (secrets, PII, fake-action claims)
                      REPORT ─► LEARN (agent_learning, business, content, experiment memory)
```

The blackboard (`RunContext.board`) is the only channel between agents. Each agent receives only the keys in its `required_context` and `inputs`. A model agent may write only the keys in its registry `outputs`; anything else is ignored and logged.

## Verification semantics

*Content checks* decide support: citation, primary-source quote match, quote, statistics, claim wording and contradiction. *Metadata checks* (date, cross-source, source quality, outdated) lower confidence by ×0.9 for each warning. The outcomes are:

- A contradiction fail makes the claim CONTRADICTED.
- Any other content-check fail makes it UNSUPPORTED.
- A content-check warn, such as a quote found only in secondary sources, makes it PARTIALLY_SUPPORTED.
- When all content checks pass, the claim is SUPPORTED and becomes a FACT.

Confidence is calculated as: source tier × corroboration × verification factor.

## Cost model

Each agent's `cost_class` sets its model tier (`config/settings.yaml`) and a unit charge: LOW=1, MEDIUM=5, HIGH=20, rule=0. Runs have a unit budget and a model-call cap. Model responses are cached by (agent, prompt version, prompt hash) with a TTL, so repeated research does not cost twice.
