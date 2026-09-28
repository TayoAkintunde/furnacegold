# Extending the system

## Add a new agent

1. Pick the family file in `agents/registry/` (or create one; see below).
2. Add one line under `agents:`. Only the fields that differ from the family `defaults` are needed:
   ```yaml
   - {id: voice_ai, name: Voice AI Researcher, focus: "speech and voice AI", keywords: [voice, speech, tts, asr]}
   ```
   The agent id becomes `research.voice_ai`. Use `extra_tools: [...]` to append to a default list instead of replacing it.
3. If the agent's behaviour can be written as code (a check, a metric, a transformation), set `executor: "rule:<name>"` and implement `@rule("<name>")` in `aibos/rules/`. Otherwise keep `executor: llm` and choose a `prompt_template` from `agents/prompts/`.
4. Run `python -m aibos agent-test research.voice_ai` and `python -m unittest discover -s tests -t .`. The registry tests check required fields, templates, rule implementations and references.
5. To get the agent selected automatically, give it `keywords` or `capabilities` that a stage pool uses (`config/stages.yaml`), or reference it in a pipeline step.

A new family file needs `family`, `domain`, `level`, `defaults` (all 17 required fields) and `agents`.

## Add a new revenue stream

1. Add an entry to `config/revenue_streams.yaml` with the agents that assess it, the evidence required before pursuing it, and the approval categories it triggers.
2. If no agent covers it, add one to `agents/registry/revenue.yaml` (for example `{id: licensing_saas, name: ..., focus: ...}`).
3. If it has measurable outcomes, add metric names to an analytics agent's `params.metrics` and export the data to `data/metrics/*.csv`.
4. `python -m aibos audit` flags any stream that references a missing agent.

## Add a new platform

1. Add the platform rules to `config/platforms.yaml`: length limits, part separator, norms, and the integration key.
2. Add a social agent: `{id: bluesky, name: Bluesky Agent, focus: "Bluesky post", params: {platform: bluesky, group: bluesky}, keywords: [bluesky]}`. Keywords must name the platform only; never use generic words like "post" or "video". For a format variant (a thread or carousel), reuse the platform's `group` and add `format_keywords: [thread]`. The variant is then chosen only when that format is named, and it replaces the plain agent.
3. Add the integration to `config/integrations.yaml` with `adapter: null`. It stays `NOT CONNECTED` until someone writes an adapter.
4. `content_quality.platform_fit` enforces the new limits automatically, and the analytics plan names the integration.

## Add or change an AI model

Models are configured, not hard-coded. Edit `config/settings.yaml`:

```yaml
models:
  HIGH_COST: {model: <model id>, effort: high, max_tokens: 16000}
pricing_per_mtok:
  <model id>: [input_usd, output_usd]
```

To add a different provider, implement a `Backend` subclass in `aibos/backends.py` with a `complete(spec, system, user) -> BackendResult` method, then register it in `get_backend`. The output contract, validation, caching and budgets apply unchanged.

## Add a new pipeline

Add it to `config/pipelines.yaml`. Each step either references a library stage (`ref: VERIFY`) or lists agents. It can also name a `post` hook from `Hooks` in `aibos/orchestrator.py`. Run it with `python -m aibos pipeline <name> "<topic>"`.

## Add a new integration adapter

1. Implement it (for example in `aibos/integrations.py`) and add its name to `IMPLEMENTED_ADAPTERS`.
2. Set `adapter:` and `env:` in `config/integrations.yaml`.
3. For publishing adapters, execution must happen only inside `ApprovalQueue._execute`, after approval, and must record what actually happened.
