# furnacegold: AI Business Operating System

furnacegold is a registry-driven multi-agent framework. It researches technology, verifies claims, turns verified knowledge into educational content, finds business opportunities, designs experiments and reports results. A human approves every external action.

```
RESEARCH → KNOWLEDGE → ANALYSIS → CONTENT → EDUCATION → AUDIENCE → LEADS → PRODUCTS
→ SERVICES → SOFTWARE → REVENUE → ANALYTICS → LEARNING → NEW RESEARCH
```

The system optimises for evidence, experimentation, customer value, learning speed, quality and risk management. **It does not promise financial results.** It also never fabricates sources, metrics, customers or actions, and it never publishes on its own.

## At a glance

- **319 agents** in 22 families, declared in YAML (`agents/registry/`):
  - 1 master orchestrator and 15 domain orchestrators
  - 88 deterministic rule agents
  - 215 model-backed agents
- **Smallest sufficient team.** Each objective activates only the stages it needs. The Part 45 demo uses 10 model agents and 28 rule checks out of 319.
- **Evidence system.** Claims start UNVERIFIED and are checked verbatim against captured sources. Only SUPPORTED claims become facts, and each fact has a full evidence chain. Conflicts are resolved in favour of primary evidence, or kept open when evidence is comparable.
- **Quality gate.** 16 content checks (factuality, hallucinated numbers, hype, clickbait, AI-slop, platform limits, plagiarism, and others). A BLOCKING issue keeps the draft out of the approval queue.
- **Human control.** Publishing, spending, launches, contracts, deletions and production changes all go through an approval queue. Approving an item records the decision; it never pretends the action ran.
- **Honest status.** Missing capabilities are reported as `NO_MODEL`, `NOT CONNECTED`, `CREDENTIAL REQUIRED` or `NO DATA`.
- **Memory, performance tracking, audit and improvement proposals.** Critical agents are never modified automatically.
- **63 unit and end-to-end tests** using only the standard library (`unittest`).

## Quick start

```bash
pip install -r requirements.txt
python -m aibos agents                                   # the registry
python -m aibos plan "Research MCP servers and write a LinkedIn post"   # dry run showing the chosen team and why
python -m aibos demo                                     # the Part 45 demonstration (scripted backend)
python -m aibos integrations                             # what is actually connected
python -m unittest discover -s tests -t .
```

To use a live model, run `pip install anthropic` and set `ANTHROPIC_API_KEY`. The `auto` backend then routes agents by cost class: LOW → Haiku 4.5, MEDIUM → Sonnet 5, HIGH → Opus 5. Change the mapping in `config/settings.yaml`.

## Layout

```
aibos/               framework (orchestrator, selection, runtime, backends, evidence, rules/, …)
agents/registry/     22 YAML agent families (the agent library)
agents/prompts/      shared output contract + 12 family prompt templates
config/              settings, stages, pipelines, platforms, integrations, brand, taxonomy, revenue streams
demo/                Part 45 demonstration: captured sources, authored responses, output report
docs/                ARCHITECTURE.md, OPERATIONS.md, EXTENDING.md
tests/               unit + end-to-end tests with fictional fixtures
data/                runtime state (git-ignored): memory, runs, approvals, experiments, metrics, cache
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/OPERATIONS.md](docs/OPERATIONS.md), [docs/EXTENDING.md](docs/EXTENDING.md) and [demo/README.md](demo/README.md).
