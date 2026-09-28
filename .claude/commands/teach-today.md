---
description: Daily teaching pipeline — find today's most teachable AI development and prepare the screen-recording brief
argument-hint: "[optional focus, e.g. coding agents]"
---
Run the daily teaching pipeline for this repository (aibos). Guiding question:
"What important thing happened in AI recently that I can demonstrate and teach people how to use?"

Focus (optional): $ARGUMENTS

1. **Capture sources.** Research agents only use captured sources, and the system's own web search is NOT CONNECTED.
   Search for the most recent developments across the areas in `config/teaching.yaml` (focus_areas).
   - Prefer primary sources: vendor docs, release notes and announcements. Add one independent source per development.
   - For each source, run `python -m aibos sources add --url <url> --publisher <name> --type primary|official_docs|news|blog --published YYYY-MM-DD`.
   - If URL fetching is blocked, write the exact text you retrieved to a JSON file in the format of `demo/teaching/sources.json` and run `python -m aibos sources import --file <file>`. Label `retrieved_by` honestly.
   - Never invent source text or dates.
2. **Run the pipeline:** `python -m aibos teach-today $ARGUMENTS`
3. **If a model-backed agent reports NO_MODEL** (no ANTHROPIC_API_KEY), tell the user. Offer to act as the model backend yourself:
   - Answer the saved prompt at `data/runs/<run>/prompts/<agent>.md`, following its output contract exactly.
   - Add the answer to a responses file whose `"provenance"` says it was authored in this Claude Code session.
   - Re-run with `--responses <file>`. Repeat stage by stage until the pipeline completes.
   - The deterministic verification, scoring and quality checks still decide what passes. Never bypass them.
4. **Show the user `teach_today.md`:** the radar, the teaching opportunities with scores and rejections, today's screen recording, and the business opportunity.
5. **Stop.** The user decides what gets recorded (`python -m aibos teaching select <id> --by <name>`). Never select, record or publish on their behalf.
