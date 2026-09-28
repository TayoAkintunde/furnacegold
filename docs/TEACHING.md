# Screen-recorded teaching: the primary workflow

> **The question:** *What important thing happened in AI recently that I can demonstrate and teach people how to use?*
> It is never *what AI news can I post today?*

```
Trend → Understanding → Demonstration → Teaching → Distribution → Audience learning → Monetization
```

Configuration lives in `config/teaching.yaml`: focus areas, scoring weights, gates, recording rules, package formats, workflow and learning metrics. The agents are defined in `agents/registry/teaching.yaml`, and the trend-discovery agents are at the end of `research.yaml`.

## The daily pipeline: `teach-today`

```bash
python -m aibos sources add --url <url> --publisher <name> --type primary --published YYYY-MM-DD   # capture sources first
python -m aibos teach-today ["coding agents"]        # same as: python -m aibos daily / Claude Code /teach-today
```

| Stage | Agents | What happens |
|---|---|---|
| TREND DISCOVERY | `research.trend_radar` | Builds today's AI radar from the captured sources, favouring what can be demonstrated over what is merely popular. |
| VERIFICATION | 8 verifiers | Checks every claim verbatim against the source text. Only SUPPORTED claims can be taught as fact. |
| TEACHING OPPORTUNITY | `teaching.opportunity_analyst`, `value_gate`, `scorer` | Answers "can I teach this?" for each development: what changed, why it matters, who should care, what you can do, how to demo it, beginner mistakes, simplest and advanced examples. Then value-gates and scores it. |
| SCREEN RECORDING PLAN | `recording_planner`, `feasibility` | Covers the hook (5–15 s), context, demonstration steps, teaching moments, proof and takeaway, and lists anything to verify before recording. |
| SCRIPT | `script_writer`, `script_quality`, `technical_check` | Writes a natural spoken script with a mistake-and-fix moment and caveats. Every model id, API or command is checked against the sources. |
| REPURPOSING | `repurposer` | Produces a repurposing *plan*. The package itself is written from the real recording. |
| BUSINESS OPPORTUNITY | `business_analyst` | Assesses eight opportunity types. Only genuine ones are listed; nothing is forced. |
| QUALITY | factuality, hallucination, hype, clickbait, AI-slop, originality, readability, value-first | A BLOCKING result keeps the item from being recommended as ready. |
| APPROVAL QUEUE | hook | Writes every opportunity to the teaching database (see below) as RESEARCHED or REJECTED. The single recommendation is marked. |

The output is `teach_today.md`, containing TODAY'S AI RADAR, TODAY'S TEACHING OPPORTUNITIES (scores and rejection reasons), TODAY'S SCREEN RECORDING (title, hook, audience, problem, demo, step-by-step plan, spoken script, takeaway and repurposing plan) and TODAY'S BUSINESS OPPORTUNITY.

### Scoring

| Criterion | Weight | Source |
|---|---|---|
| newness | 0.18 | **computed** from the newest verified date that is not in the future |
| practical usefulness | 0.17 | judged; needs a written justification, otherwise 0 |
| educational value | 0.15 | judged + structure (mistakes, simple example, advanced example) |
| demonstrability | 0.15 | judged; 0 if it cannot be shown on screen |
| audience interest | 0.10 | **computed** from the learning loop and repeated viewer questions; NO DATA = neutral 0.5 |
| meaningful result | 0.10 | judged; 0 without a concrete "what you'll build" |
| business value | 0.07 | judged |
| evidence quality | 0.08 | **computed**: share of the topic's claims that are verified × their confidence |

**Hard gates.** A topic is rejected if any of these hold:
- it fails value-first
- it has no verified claim
- evidence quality is below 0.5
- demonstrability is below 0.4
- total score is below 0.55
- you have already selected or recorded it

If nothing passes, the report says so. Recording nothing beats recording something weak.

## `record <id>`: the full recording package

Run it only after you choose the topic:

```bash
python -m aibos teaching select <id> --by <you>
python -m aibos record <id> [--regenerate]
```

It reuses teach-today's plan and script unless you pass `--regenerate`. It then adds the beginner, intermediate and advanced versions and the production details: setup, accounts and costs, test data, shot list, callouts, chapters, title and thumbnail options, and a description with resources.

The package is re-checked, written to `data/teaching/<id>/recording_package.md`, and the item moves to READY_TO_RECORD. If anything is blocking, it stays SELECTED and the report lists why.

## `content-from-recording <id> --transcript FILE`

Record the video yourself, then run:

```bash
python -m aibos content-from-recording <id> --transcript recording.srt --by <you>
```

The transcript may be `.srt`, `.vtt`, or `.txt` with or without `[mm:ss]` stamps. It becomes the source of truth: numbers spoken in it count as grounded, and the analyst flags anything said on camera that no verified claim backs.

The package has 14 formats:
- YouTube tutorial, YouTube Short, TikTok, Instagram Reel
- LinkedIn post, X post, X thread
- newsletter section, blog tutorial, carousel concept
- FAQ, checklist, downloadable resource, course lesson

Each has its own purpose, audience and value statement. The checks cover:
- platform limits
- overlap between formats (adapt, don't duplicate)
- value-first
- factuality and hallucination
- hype, clickbait and AI-slop
- plagiarism

Every piece goes to `python -m aibos approvals list`. Nothing is published.

## Workflow and human control

```
RESEARCHED → SELECTED → READY_TO_RECORD → RECORDED → EDITING → READY_TO_PUBLISH → PUBLISHED → ANALYZED   (+ REJECTED)
```

| Transition | Who |
|---|---|
| RESEARCHED, READY_TO_RECORD, ANALYZED | system, after its own work succeeds |
| SELECTED, RECORDED, EDITING, READY_TO_PUBLISH, PUBLISHED, REJECTED | **you** (`teaching select / advance / reject --by <you>`) |

PUBLISHED requires `--url` pointing to where *you* published. Transitions cannot skip a state or go backwards, and every one is kept in the item's history.

## Learning loop: `teaching analyze [<id>]`

After you publish, the system reads two kinds of data you supply:
- **Metrics:** CSV files in `data/metrics/`, with `asset_id` set to the teaching id. Supported metrics: views, retention_rate, avg_view_duration_s, watch_time_h, saves, shares, comments, clicks, followers_gained, leads, conversions, plus a retention curve as `retention_at_<N>s`.
- **Comments:** files matching `data/feedback/<id>*.txt`.

It works out:
- the biggest retention drop-off (where viewers left)
- repeated viewer questions, which become candidate next lessons
- hook retention at 15 s
- relative performance by category, once at least two videos have data

These results feed back into audience interest when topics are scored. With no data, it reports NO DATA.

## The content database

Each teaching item (`data/teaching/opportunities.jsonl`) holds:
- **Discovery:** topic, trend, date discovered, sources, source quality, what changed
- **Teaching design:** audience, problem solved, teaching angle, demo idea, difficulty, estimated recording time
- **Production:** recording plan, script, content formats
- **Opportunities:** product, service, course and affiliate
- **After publishing:** performance and lessons learned

It also stores the verified claims (so later commands can re-check facts), the score breakdown, the gate reasons and the full workflow history.

## Claude Code slash commands

`.claude/commands/teach-today.md`, `record.md` and `content-from-recording.md` run the CLI.

When no model backend is connected, they let Claude Code act as the backend openly. It answers the saved prompts one agent at a time, into a responses file marked as authored in the session. The deterministic checks still decide what passes.
