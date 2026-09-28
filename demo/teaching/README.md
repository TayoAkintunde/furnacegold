# Screen-recorded teaching example (current AI topic, 2026-09-28)

This example runs the three teaching commands on real developments from the week of 2026-09-28:

| Step | Command | Output |
|---|---|---|
| 1 | `/teach-today` | [`output/1_teach_today.md`](output/1_teach_today.md) |
| 2 | `/record <id>` | [`output/2_recording_package.md`](output/2_recording_package.md) |
| 3 | `/content-from-recording <id> --transcript …` | [`output/3_content_package.md`](output/3_content_package.md) |

Reproduce it with `demo/teaching/run_example.sh`.

## What is real, and what is not

| Part | Status |
|---|---|
| **Developments** | **Real, researched on 2026-09-28:** Google's updated Gemini API managed agents (`antigravity-preview-09-2026`, Files API, Credentials API); Claude Fable 5.1 arriving in Claude Code; the Sora API shutdown. |
| **Sources** ([`sources.json`](sources.json)) | Real. Each is a search-engine extract restricted to one publisher's domain. Direct page fetches are blocked in this environment, so these are extracts, not full pages. Dates appear only where the source shows them. |
| **Model-backed agent outputs** ([`build_responses.py`](build_responses.py)) | **Authored by the Claude Code session operator acting as the model backend**, because no Anthropic API key is available in this environment. They use only `sources.json`, and every output carries that provenance. |
| **Deterministic checks** | **Ran for real:** verification (14 claims → 12 verified), value gate, eight-criteria scoring, demonstration feasibility, script quality, technical-identifier verification, factuality, hallucination, hype, AI-slop, platform limits, package overlap, and security. |
| **Topic selection** | **A demo-operator action**, recorded as such in the item's history. In your workflow, only you select topics. |
| **Transcript** | **Not a real recording.** [`SCRIPT_READTHROUGH_NOT_A_REAL_RECORDING.vtt`](SCRIPT_READTHROUGH_NOT_A_REAL_RECORDING.vtt) is a timed read-through of the generated script. It only demonstrates the `/content-from-recording` mechanics. Use your own transcript for real content. |
| **Publishing** | **None.** 14 drafts are PENDING in the approval queue. |
| **Analytics** | **None yet.** Performance and lessons stay empty until you publish and export metrics. |

## What the system decided

The three developments scored as follows.

| Rank | Development | Score | Decision |
|---|---|---|---|
| 1 | **Build a Gemini managed agent that cleans a file in its own sandbox (AI Studio, then Python)** | 0.836 | Recommended |
| 2 | Choose the right effort level for Claude Fable 5.1 in Claude Code | 0.669 | Worth demonstrating, but lower on demonstrability and meaningful result |
| 3 | Sora API shutdown | 0.371 | Rejected: important news, but nothing can be demonstrated, and it fails the value-first gate |

Several things were kept out or flagged along the way:

- **Weak evidence excluded.** Two claims never became facts: an unattributed "40% fewer output tokens" figure and a blog-only free-tier statement. Neither appears in the script.
- **Technical check flagged a guessed method.** `client.interactions.create()` does not appear in the sources, which only say "create an interaction". It is listed under *verify before recording*.
- **Business opportunities (two genuine, low-cost):** a practice-pack digital product and a file-clean-up automation service. Course, consulting, SaaS and affiliate were judged not genuine and were not forced.
