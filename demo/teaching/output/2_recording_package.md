# Recording package — Let a Gemini agent clean your messy CSV — AI Studio, then Python

_Teaching item `tch_c187c188ff` · status after this run: **READY_TO_RECORD** · run `20260928T142941Z_53a4d9` · backend: scripted (scripted: authored 2026-09-28 by the Claude Code session operator acting as the model backend (no Anthropic API key in this environment); grounded only in demo/teaching/sources.json)_

> **The question this system asks:** *What important thing happened in AI recently that I can demonstrate and teach people how to use?* — not *what AI news can I post today?*

## 1. Before you press record

**Setup:**
- [ ] Close unrelated tabs and notifications
- [ ] Sign in to AI Studio before recording
- [ ] Create sales_messy.csv (fictional data only)
- [ ] Prepare the Python script in an editor, with the key loaded from an environment variable, never on screen
- [ ] Zoom the browser and terminal to a readable size

**Accounts and costs:**
- [ ] Google AI Studio account
- [ ] Gemini API key — check current pricing and free-tier limits before recording

**Test data:**
- [ ] sales_messy.csv: about forty rows, blank rows, three date formats, prices with currency symbols as text

## 2. Recording plan

**Hook (11s):** In the next ten minutes you'll give a Gemini agent a messy spreadsheet, let it clean the data in its own sandbox, and download the fixed file.

**Context:** Google updated the managed agents in the Gemini API (antigravity-preview-09-2026, on Gemini 3.8 Flash) and added a Files API and a Credentials API. A managed agent is one Google runs for you: it plans, runs code, checks the result and repeats until the task is done.

**Audience:** developers and technical operators; no-code builders for the first half  ·  **Problem:** cleaning and analysing files with an agent without building your own code-execution sandbox  ·  **Difficulty:** beginner  ·  **Estimated recording time:** 12 min

**Prerequisites:** Google account with AI Studio access; Gemini API key (for the Python part); Python with the Google GenAI client installed; sales_messy.csv — a made-up file with blank rows, mixed date formats and prices typed as text

| Step | On screen | Say | Why |
|---|---|---|---|
| 1 | Google AI Studio home, then click the Agents tab and scroll the template list | These templates are the base Antigravity agent with tools and settings pre-configured. | orient beginners before any code |
| 2 | Open the base Antigravity agent template and show its tool and environment settings | This is where the agent's sandbox and tools are configured. | makes the sandbox concrete |
| 3 | Open sales_messy.csv in a spreadsheet: blank rows, three date formats, prices as text | Here's our starting point, a file I made up for this video. | starting state for the before/after proof |
| 4 | Attach sales_messy.csv to the agent and type the task: clean it, standardise dates, convert prices, summarise the changes | One file, one instruction. | the simplest useful example |
| 5 | Watch the agent's steps: it writes Python, runs it, reads the output and corrects itself | Plan, act, check, repeat. | teaching moment: the agent loop |
| 6 | Download the cleaned file and the change summary; open both next to the original | Same data, fixed. | proof |
| 7 | Terminal: a short Python script that creates an interaction with agent antigravity-preview-09-2026, environment remote, then prints `interaction.output_text` and `interaction.environment_id`; the client call shown as `client.interactions.create()` | Now the same thing from code. | moves the viewer from playground to something they can automate |
| 8 | Second request asking for a monthly sales chart: first without the environment id (file not found), then with it (chart created) | This is the mistake almost everyone makes. | mistake and correction; teaches environment ids |
| 9 | Slide with the limitations and the Credentials API note | A few honest caveats. | limitations |

**Teaching moments (pause and explain):**
- after step 2: what a sandbox is: a temporary Linux machine that exists only for this agent's task
- after step 5: the plan-act-check loop, and why the agent can fix its own errors
- after step 8: interaction id vs environment id: the environment id is what keeps your files between requests
- after step 9: why secrets go in the Credentials API, never in the prompt

**Proof (show the real result):** The original CSV and the downloaded cleaned CSV side by side, plus the agent's written summary of every change, and the chart from the second request.

**Useful variation:** Reuse the same environment for a second request, a monthly sales chart built from the cleaned file.

**Limitations to say out loud:** preview service: names and limits can change; antigravity-preview-05-2026 is deprecated on October 5, 2026 (requests redirect to the new harness); pricing and free-tier limits not confirmed from a Google source; do not upload sensitive data to a preview service

**Takeaway:** You can now hand a Gemini managed agent a file, let it do the work in its own sandbox, and pull the result back out, first in AI Studio and then from Python.

**Verify on screen before recording:**
- [ ] current pricing and free-tier limits for managed agents (only a blog claims free-tier access)
- [ ] exact Python client method name for creating an interaction (the docs extract only says 'create an interaction')
- [ ] where the file-attach control is in the AI Studio Agents playground
- [ ] that antigravity-preview-09-2026 is still the current agent id on recording day

**Plan checks:**
- quality score 0.938 — **no blocking issues**
- warning: technical_check: not found in verified sources — check on screen before recording: ['client.interactions.create()']

## 3. Spoken script

**[HOOK]**

In the next ten minutes you'll give a Gemini agent a messy spreadsheet, let it clean the data in its own sandbox, and download the fixed file.

**[CONTEXT]**

Here's what changed. Google updated the managed agents in the Gemini API. The new version is called antigravity-preview-09-2026, it replaces the May version, and it runs on Gemini 3.8 Flash. Two new pieces matter for us. A Files API, so you can put files into the agent's sandbox and get results back out. And a Credentials API, so the agent can use your services without the model ever seeing your keys. A managed agent just means Google runs the agent for you. You send a task, and it plans, runs code, checks the result and keeps going until it's done.

**[DEMO — step 1]**

Let's start in Google AI Studio. I'm opening the Agents tab. You can see a list of templates here. They're the base Antigravity agent with some tools and settings already switched on.

**[DEMO — step 2]**

I'll open the base template. This panel is where the tools and the environment are set. The environment is the sandbox: think of it as a temporary Linux computer that exists only for this task.

**[DEMO — step 3]**

This is our starting point. It's a sales file I made up for this video. There are blank rows, dates written three different ways, and some prices typed as text. Nothing real in here, and that matters, because whatever you upload goes into the sandbox.

**[DEMO — step 4]**

I attach the file and give it one instruction: clean this file, make every date the same format, turn the prices into numbers, and tell me what you changed.

**[TEACHING_MOMENT — step 5]**

Now watch the steps while it works. It wrote a small Python script, ran it, read the output, noticed one column was still text, and fixed it. That loop is the whole idea: plan, act, check, repeat. You didn't install anything on your machine.

**[PROOF — step 6]**

And here's the result. On the left, the original file with the gaps and the mixed dates. On the right, the cleaned file I just downloaded from the sandbox, and underneath, the agent's summary of every change it made.

**[DEMO — step 7]**

Now the same thing from code, because that's how you'd use this for real. You create an interaction, set the agent to antigravity-preview-09-2026, pass your input, and set the environment to remote. Then you print the final answer and the environment ID. Check the current docs for the exact client call, because this is still a preview.

**[MISTAKE — step 8]**

Now I'll ask for a chart of monthly sales. And it can't find the file. That's my mistake, and it's the one almost everyone makes. I didn't pass the environment ID, so this request started a brand-new sandbox, and my file isn't in it. The docs say to store the interaction ID and the environment ID. So I pass the environment ID and run it again. There's the chart, built from the same cleaned file.

**[CAVEAT — step 9]**

A few honest caveats. This is a preview, so names and limits can change. If you built on the older May version, it's deprecated on October 5, 2026, and requests get redirected to the new one. I haven't confirmed pricing or free-tier limits from Google, so check those before you rely on this. And never paste real keys into a prompt. That's exactly what the Credentials API is for.

**[TAKEAWAY — step 9]**

So now you can hand a Gemini managed agent a file, let it do the work in its own sandbox, and pull the result back out, first in AI Studio and then from Python. Try it on a messy file of your own, and keep that environment ID.

**Script checks:**
- quality score 1.0 — **no blocking issues**

## 4. Multi-level versions

### Beginner: What is a Gemini managed agent? Clean a CSV in AI Studio (no code)
- *Question:* What is this and how do I use it?
- *Promise:* Use an AI Studio agent template to clean a file and download the result.
- *Demo:* steps 1-6 of the plan, no Python
- *Outcome:* a cleaned CSV and a plain-English idea of what a sandbox is
- *Value:* After this you can use an AI Studio agent template to clean a messy CSV without writing code.
- *Length:* ~7 min

### Intermediate: Automate a weekly file clean-up with the Gemini Interactions API
- *Question:* How can I use this to solve a real problem?
- *Promise:* Script the same job in Python and keep working in one sandbox across requests.
- *Demo:* steps 7-8, plus a second file
- *Outcome:* a reusable Python script that uploads, cleans, charts and downloads
- *Value:* After this you can run a managed agent from Python and reuse its sandbox with the environment id.
- *Length:* ~12 min

### Advanced: A production-shaped file agent: Files API, Credentials API and scheduled runs
- *Question:* How can I build a serious workflow/system with this?
- *Promise:* Design a scheduled job that feeds exports to the agent, stores results, and uses registered credentials for a connected service.
- *Demo:* architecture sketch, credential registration, a scheduled run, failure handling
- *Outcome:* a runnable design with secrets kept out of prompts
- *Value:* After this you can design a scheduled file-processing agent that keeps secrets out of the prompt using the Credentials API.
- *Length:* ~20 min

## 5. Production

| Shot | On screen | Seconds |
|---|---|---|
| 1 | face or title card with the before/after spreadsheet | 12 |
| 2 | AI Studio Agents tab and template settings | 60 |
| 3 | messy CSV, attach, task prompt | 60 |
| 4 | agent steps running | 90 |
| 5 | before/after side by side | 45 |
| 6 | Python script and output | 120 |
| 7 | environment-id mistake and fix | 90 |
| 8 | caveats slide | 45 |

**On-screen callouts:**
- Sandbox = temporary Linux machine for this task
- Store the environment ID
- Keys go in the Credentials API, not the prompt
- Preview: check pricing

**Chapters:**
- 00:00 The result
- 00:15 What changed
- 01:10 AI Studio agent templates
- 03:00 Cleaning the file
- 05:30 Before and after
- 06:30 Same thing in Python
- 08:30 The environment ID mistake
- 10:00 Caveats

**Title options:**
- Let a Gemini agent clean your messy CSV (AI Studio + Python)
- Gemini managed agents: give it a file, get a better file back
- The one setting that keeps your files between Gemini agent requests

**Thumbnail text options:**
- MESSY CSV → CLEAN
- Agent does the cleanup
- Don't lose your files

**Description:**

Google updated Gemini API managed agents (antigravity-preview-09-2026) and added a Files API and a Credentials API. In this tutorial you give an agent a messy spreadsheet in AI Studio, watch it clean the data in its own sandbox, download the result, then do the same from Python and keep working in the same sandbox with the environment ID. Caveats: preview service; check pricing and free-tier limits; never paste keys into prompts.

**Resources to link:**
- https://ai.google.dev/gemini-api/docs/antigravity-agent
- https://aistudio.google.com/learn/managed-agents-updated-harness-files-credentials
- practice pack: sales_messy.csv + task prompt (to be created)

## 6. Evidence

| Claim | Verification | Confidence | Sources |
|---|---|---|---|
| g1: Google released the antigravity-preview-09-2026 managed-agent harness, which replaces antigravity-preview-05-2026. | SUPPORTED | 0.693 | s1 |
| g2: The updated harness runs on Gemini 3.8 Flash, with the model configurable per interaction. | SUPPORTED | 1.0 | s2, s4 |
| g3: A new Files API lets you upload into a running sandbox, list what the agent wrote, and download the files you need. | SUPPORTED | 1.0 | s2, s4 |
| g4: A new Credentials API lets you register secrets once and attach them to an MCP server or a sandbox environment variable without the model seeing them. | SUPPORTED | 0.729 | s2 |
| g5: Google AI Studio's playground and Agents-tab templates let you prototype managed agents without writing API calls. | SUPPORTED | 0.693 | s3 |
| g6: Each call can provision a Linux sandbox where the agent can run Bash, Python and Node.js commands, install packages and run tests. | SUPPORTED | 0.693 | s1 |
| g7: From code, you create an interaction with the agent set to antigravity-preview-09-2026 and the environment set to remote, and store interaction.environment_id to keep using the same sandbox. | SUPPORTED | 0.693 | s1 |
| g8: antigravity-preview-05-2026 will be deprecated on October 5, 2026, after which requests to it are redirected to the updated harness. | SUPPORTED | 0.729 | s2 |

## Next

Record it yourself, then run:
`python -m aibos content-from-recording tch_c187c188ff --transcript <transcript.srt|.vtt|.txt> --by <you>`
