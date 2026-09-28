# CLAUDE.md

AI Business Operating System (`aibos`): a registry-driven multi-agent framework. Python 3.10+, stdlib + PyYAML; `anthropic` is optional.

**Primary purpose: screen-recorded teaching.** The question is "What important thing happened in AI recently that I can demonstrate and teach people how to use?", not "what AI news can I post?". Main commands: `teach-today`, `record <id>`, `content-from-recording <id> --transcript FILE`, `teaching …`. Configuration is in `config/teaching.yaml`, and the guide is `docs/TEACHING.md`. Claude Code slash commands live in `.claude/commands/`.

## Commands
- Tests: `python -m unittest discover -s tests -t .` (must stay green; tests isolate state via `AIBOS_DATA_DIR`)
- CLI: `python -m aibos <command>`; see `docs/OPERATIONS.md`. Dry-run team selection: `python -m aibos plan "<objective>"`
- Registry sanity: `python -m aibos agents`, `python -m aibos audit`

## Layout
- `aibos/`: framework. `orchestrator.py` (master + domain orchestrators, stage hooks), `selection.py` (profiling + team selection), `runtime.py` (runs one agent), `backends.py` (anthropic/offline/scripted), `rules/` (deterministic agents), `evidence.py`, `memory.py`, `approval.py`, `reports.py`, `cli.py`
- `agents/registry/*.yaml`: agent definitions (family `defaults` + one line per agent). `agents/prompts/`: the output contract and family templates
- `config/`: settings (models, budgets, team sizes, approval categories), stages, pipelines, platforms, integrations, brand, taxonomy, revenue streams
- `data/`: runtime state (git-ignored). `demo/`: Part 45 demonstration (`demo/data/` is git-ignored)

## Business profile
`config/business_profile.yaml` holds the owner's real business context, and `aibos/profile.py` validates it. Never fill it with assumed values: only transcribe the owner's answers to `docs/BUSINESS_QUESTIONNAIRE.md`, and have the owner confirm them before applying.

## Invariants (do not break)
- Never fabricate sources, metrics, customers, results or actions. Missing capability → `NO_MODEL` / `NOT CONNECTED` / `CREDENTIAL REQUIRED` / `NO DATA`.
- Claims enter UNVERIFIED. Only verification makes a claim FACT (`evidence.aggregate_verification`).
- Model agents may only write the blackboard keys listed in their registry `outputs`.
- External actions (publish, spend, launch, contracts, deletion, production changes) go only through `ApprovalQueue`. Approval never marks an action executed without a real adapter.
- Improvement proposals are never auto-applied. Agents marked `critical: true` are never auto-modified.
- Teaching workflow: the system only sets RESEARCHED, READY_TO_RECORD and ANALYZED. SELECTED, RECORDED, EDITING, READY_TO_PUBLISH and PUBLISHED belong to the owner. Never write or invent a recording transcript.
- Every piece of content needs a specific `value_statement` (`content_quality.value_first`).
- Add agents by YAML, not code. A new rule needs `@rule("name")` in `aibos/rules/`. Registry tests check every reference.
