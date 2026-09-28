# furnacegold: AI Business Operating System

## Primary purpose: screen-recorded teaching

The system finds the latest important developments in AI and emerging technology, works out what they actually do, and turns them into screen-recorded lessons that teach people how to use them.

The question it asks is:

> **"What important thing happened in AI recently that I can demonstrate and teach people how to use?"**

It does not ask "what AI news can I post today?"

```
Trend → Understanding → Demonstration → Teaching → Distribution → Audience learning → Monetization
```

| Command | What it does |
|---|---|
| `python -m aibos teach-today [focus]` (also `/teach-today`, `daily`) | Trend discovery → verification → "can I teach this?" analysis → scoring → recording plan → spoken script → repurposing plan → business opportunity → teaching queue |
| `python -m aibos record <id>` (also `/record`) | Takes a topic **you** selected and produces the full recording package: pre-record checklist, plan, script, beginner/intermediate/advanced versions, shot list, chapters, titles and description |
| `python -m aibos content-from-recording <id> --transcript FILE` (also `/content-from-recording`) | Takes your finished recording's transcript and produces 14 adapted formats, each quality-checked and queued for your approval |
| `python -m aibos teaching list\|show\|select\|reject\|advance\|analyze` | Manages the workflow: RESEARCHED → SELECTED → READY_TO_RECORD → RECORDED → EDITING → READY_TO_PUBLISH → PUBLISHED → ANALYZED |

Topics are scored on eight criteria, in this order of weight: newness, practical usefulness, educational value, demonstrability, audience interest, meaningful result, business value, evidence quality. A topic is rejected if the evidence is weak, it cannot be demonstrated, or it fails the value-first rule. The value-first rule means every piece must say what the viewer can now do, solve, build, understand or avoid.

Nothing is recorded or published automatically. The learning loop feeds real metrics and repeated viewer questions back into topic selection.

See [docs/TEACHING.md](docs/TEACHING.md), and [demo/teaching/](demo/teaching/README.md) for a worked example on a current topic.

The system optimises for evidence, experimentation, customer value, learning speed, quality and risk management. **It does not promise financial results.** It also never fabricates sources, metrics, customers or actions, and it never publishes on its own.

## At a glance

- **345 agents** in 23 families, declared in YAML (`agents/registry/`):
  - 1 master orchestrator and 16 domain orchestrators (the 15 from the spec, plus Teaching)
  - 98 deterministic rule agents
  - 230 model-backed agents
  - 17 of the agents form the `teaching` family
- **Smallest sufficient team.** Each objective activates only the stages it needs. The Part 45 demo uses 10 model agents and 29 rule checks; teach-today uses 6 model agents.
- **Evidence system.** Claims start UNVERIFIED and are checked verbatim against captured sources. Only SUPPORTED claims become facts, and each fact has a full evidence chain. Conflicts are resolved in favour of primary evidence, or kept open when evidence is comparable.
- **Quality gate.** 17 content checks: factuality, hallucinated numbers, hype, clickbait, AI-slop, platform limits, plagiarism, value-first, and others. A BLOCKING issue keeps the draft out of the approval queue.
- **Human control.** Publishing, spending, launches, contracts, deletions and production changes all go through an approval queue. Approving an item records the decision; it never pretends the action ran.
- **Honest status.** Missing capabilities are reported as `NO_MODEL`, `NOT CONNECTED`, `CREDENTIAL REQUIRED` or `NO DATA`.
- **Memory, performance tracking, audit and improvement proposals.** Critical agents are never modified automatically.
- **87 unit and end-to-end tests** using only the standard library (`unittest`).

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
