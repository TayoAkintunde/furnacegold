# Operations

All commands are `python -m aibos <command>`. A leading slash also works: `python -m aibos /research ...`.
Runtime state lives in `data/`, which is git-ignored. Override the location with `AIBOS_DATA_DIR`.

## Setup

```bash
pip install -r requirements.txt           # PyYAML
pip install anthropic                     # optional: enables the model backend
export ANTHROPIC_API_KEY=...              # or `ant auth login`; otherwise LLM agents report NO_MODEL
python -m aibos integrations              # shows what is actually connected
```

Without a model backend the system still runs. Rule agents do real work; model agents report `NO_MODEL` and save their prompts to `data/runs/<run>/prompts/`. Evidence-dependent stages are skipped and the run says so.

## Business profile

The agents are not tailored to your business until you answer `docs/BUSINESS_QUESTIONNAIRE.md`. Answer it in chat, or edit `config/business_profile.yaml` directly.

```bash
python -m aibos profile          # which sections are answered, plus validation errors and warnings
```

Empty fields mean UNKNOWN and are never guessed. Every run report shows the profile status.

## Feeding it sources

Research agents only use **captured sources**. No web-search adapter is connected yet.

```bash
python -m aibos sources add --url https://example.com/post --publisher Example --type primary --published 2026-09-01
python -m aibos sources add --file notes.txt --publisher "My notes" --type unknown
python -m aibos sources import demo/sources.json
python -m aibos sources list
```

Source types, from strongest to weakest: `primary`, `official_docs`, `paper`, `repository`, `news`, `analysis`, `blog`, `social`, `unknown`.

## Daily workflow (Part 37)

```bash
python -m aibos daily "AI agents"          # uses data/sources/sources.json
```

The daily pipeline runs these stages in order:

1. Source security scan
2. Research new developments
3. Verify findings
4. Update knowledge (plus gap and staleness checks)
5. Emerging opportunities
6. Content opportunities
7. Education opportunities (learning paths)
8. Product opportunities
9. Draft platform content
10. Quality checks
11. Build the approval queue
12. Analyse previous performance from `data/metrics/`
13. Agent evaluation and recommendations
14. Security scan
15. Report and learning

**Nothing is published.** Review the queue with `python -m aibos approvals list`.

Scheduling: `python -m aibos agent-test automation.scheduler` prints cron lines. Nothing is installed automatically; add them yourself with `crontab -e`.

## Weekly workflow (Part 38)

```bash
python -m aibos weekly
```

The weekly report covers content performance, social and email analytics, trends and anomalies, revenue data, experiments, customer feedback, and agent health (evaluation and audit). It is built from memory, the experiment store, `data/metrics/*.csv` and `data/feedback/*`. When a section has no data, it prints **NO DATA** rather than inventing numbers.

Metrics CSV format (`data/metrics/*.csv`):

```
date,channel,asset_id,metric,value
2026-09-29,linkedin,social.linkedin-1,impressions,1234
```

## Approvals (Part 42)

```bash
python -m aibos approvals list [--all]
python -m aibos approvals show <id>
python -m aibos approvals approve <id> --by "your name"
python -m aibos approvals reject <id>
```

Drafts with BLOCKING quality or security issues cannot be approved.

An approved item is recorded as `APPROVED` with `execution: NOT_EXECUTED` and the integration status. No publishing adapter exists yet, so publish the payload manually, then export its metrics.

## Experiments

```bash
python -m aibos experiment list
python -m aibos experiment show --id <id>
python -m aibos experiment result --id <id> --conv-a 30 --n-a 1000 --conv-b 52 --n-b 1000 --next-action "..."
```

## Agents, audit, learning

```bash
python -m aibos agents [--family research]
python -m aibos agent-status [agent_id]
python -m aibos agent-test <agent_id>
python -m aibos audit [--propose]
python -m aibos correct <agent_id> <run_id> "what was wrong"
```

`audit --propose` writes proposals to `data/proposals/proposals.jsonl` with status `PENDING_HUMAN_REVIEW`. Nothing is edited automatically.

## Other commands

`research`, `content`, `teach [--level]`, `opportunities`, `product`, `service`, `saas`, `revenue`, `trends`, `competitors` and `market` each take a topic and run through the master orchestrator. The other commands are:

- `run "<any objective>"`
- `plan "<objective>"` (dry run showing the team and reasons)
- `pipeline [name]`
- `repurpose <run_dir> [platforms]`
- `analytics`
- `knowledge [query]`
- `demo`

Common flags:

- `--sources FILE`
- `--responses FILE` (scripted backend)
- `--backend auto|anthropic|offline`
- `--complexity simple|medium|complex`
- `--no-persist`
- `--json`

## Tests

```bash
python -m unittest discover -s tests -t .
```
