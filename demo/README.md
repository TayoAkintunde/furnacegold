# Part 45 demonstration

**Task:** "Find an important recent development in AI, research it, verify it, explain it to a beginner, turn it into several pieces of content, identify potential business opportunities, design one validation experiment, and produce a weekly-style opportunity report."

Run it with `python -m aibos demo`. The full output is in [`output/report.md`](output/report.md).

## What was real, and what was not

| Part of the run | How it was done |
|---|---|
| Choosing the development | Real web search on 2026-09-28. Result: **OpenAI discontinued the Sora API on September 24, 2026.** |
| Source capture | This environment's network policy blocked direct page fetches (shell `urllib` → proxy 403; WebFetch → EGRESS_BLOCKED for help.openai.com, en.wikipedia.org, pasqualepillitteri.it). Sources were captured with **one domain-restricted web search per publisher**. Each source's text is the search engine's extract of that publisher's page, **not the full page**. Publication dates were not visible, so they are blank rather than guessed. See [`sources.json`](sources.json). |
| Model-backed agents (10) | No Anthropic SDK or API key is available here. Their outputs in [`responses.json`](responses.json) were **authored by the Claude Code session operator acting as the model backend**, using only `sources.json`. Every output carries that provenance. |
| Deterministic agents (28) | **Ran for real:** source security, 8 verifiers, knowledge storage, 9 content-quality checks, experiment registrar, analytics plan, security scans, report and learning. |
| Publishing | **Nothing was published.** Three drafts and the experiment's landing page are `PENDING` in the approval queue. All publishing integrations are `NOT CONNECTED`. |
| Analytics | **No metrics exist**, so the report says NO DATA. The analytics plan lists what to measure and where the data must come from. |

## The chain

1. **RESEARCH.** `research.ai_news` proposed 9 atomic claims, each with verbatim quotes and source ids.
2. **VERIFY.** 8 rule verifiers checked the claims against the captured text.
   - 4 claims are **SUPPORTED → FACT**. They are quoted from OpenAI's own help-center page: API shutdown on Sep 24 2026; app/web shutdown on Apr 26 2026; export advice; data deletion.
   - 5 claims are **PARTIALLY_SUPPORTED**. They rest on one blog each: removed model aliases, "no replacement named", six-month notice, alternatives, and a $1M/day cost estimate. These were kept as open questions and **excluded from the drafts**.
3. **KNOWLEDGE.** 4 verified entries went to global memory with evidence chains. 5 open questions went to project memory.
4. **TEACH.** A beginner explanation covering what an API is, what a dependency is, an example and takeaways. Flesch reading ease is 79.
5. **CONTENT.** 3 angles and 3 platform-native drafts: a LinkedIn post, a 7-part X thread and a newsletter issue. All pass the quality checks: no unverified claims, no numbers missing from verified sources, no hype or clickbait, and within platform limits.
6. **OPPORTUNITY.** 3 hypotheses:
   - Sora migration sprint (confidence 0.3; the window has already closed)
   - **model-deprecation readiness kit + audit** (0.45, selected)
   - deprecation-watch newsletter (0.35)
7. **PRODUCT.** The MVP is a free readiness kit plus an optional manual review call. Nothing gets built until demand is shown.
8. **EXPERIMENT.** A pre-registered demand test for the kit:
   - Success: ≥5% request rate with ≥200 visitors AND ≥3 calls in 14 days.
   - Failure: <2%, or 0 calls.
   - Fewer than 200 visitors counts as INCONCLUSIVE.
   - Result: NOT RUN.
9. **ANALYTICS PLAN.** Metrics per draft and for the experiment. Each integration is marked NOT CONNECTED, and data is to be imported through `data/metrics/*.csv`.
10. **WEEKLY-STYLE REPORT.** Developments, opportunities, experiments, risks and open questions. NO DATA sections are marked as such.

The same objective run with `--backend offline` is in [`output/offline_console.txt`](output/offline_console.txt). Research reports NO_MODEL, and every evidence-dependent stage is skipped with a reason.

## Files

- `sources.json`: captured sources with provenance notes
- `responses.json`: operator-authored model outputs with provenance
- `output/report.md`: the full chain report, including evidence chains, drafts, experiment and the weekly section
- `output/run.json`: machine-readable run with claims, blackboard, conflicts and all agent outputs
- `output/prompts/`: the exact prompts each model-backed agent would send to a live model
- `output/console.txt`, `output/approval_queue.txt`, `output/audit.txt`, `output/integrations.txt`
