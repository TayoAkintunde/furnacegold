# Teach Today — 2026-09-28

> **The question this system asks:** *What important thing happened in AI recently that I can demonstrate and teach people how to use?* — not *what AI news can I post today?*

_Run `20260928T142940Z_71041c` · backend: scripted (scripted: authored 2026-09-28 by the Claude Code session operator acting as the model backend (no Anthropic API key in this environment); grounded only in demo/teaching/sources.json) · nothing was recorded or published._

## TODAY'S AI RADAR

1. **Gemini API managed agents: updated Antigravity harness (antigravity-preview-09-2026) plus new Files and Credentials APIs** (AI agents) — usable today in AI Studio and from Python; a real task can be run and its output file downloaded on screen [claims: g1, g2, g3, g4, g5, g6, g7, g8]
2. **Claude Fable 5.1 available in Claude Code (1M context, effort levels)** (Claude / Claude Code) — effort levels can be compared on one real coding task [claims: f1, f2, f3]
3. **Sora API shut down** (AI models) — important news, but there is nothing left to demonstrate [claims: o1]

## TODAY'S TEACHING OPPORTUNITIES

| Opp | Topic | Score | Value gate | Decision |
|---|---|---|---|---|
| t1 | Build a Gemini managed agent that cleans a file in its own sandbox (AI Studio, then Python) | 0.836 | PASS | worth demonstrating |
| t2 | Choose the right effort level for Claude Fable 5.1 in Claude Code on one real task | 0.669 | PASS | worth demonstrating |
| t3 | What the Sora API shutdown means | 0.371 | FAIL | REJECTED: value-first: cannot say specifically what the viewer can now do; cannot be demonstrated on screen with a meaningful result; analyst: important news, but there is nothing to demonstrate; not a screen-recording topic; total score 0.371 below 0.55 |

- **t1** breakdown: newness 0.80, evidence_quality 0.78, practical_usefulness 0.75, business_value 0.75, educational_value 1.00, demonstrability 1.00, meaningful_result 1.00, audience_interest 0.50
  - notes: newest verified date 2026-09-19 (9 days); audience interest: NO DATA yet (neutral 0.5) — improves once published videos are analysed
- **t2** breakdown: newness 0.80, evidence_quality 0.76, practical_usefulness 0.75, business_value 0.50, educational_value 0.85, demonstrability 0.50, meaningful_result 0.50, audience_interest 0.50
  - notes: newest verified date 2026-09-04 (24 days); audience interest: NO DATA yet (neutral 0.5) — improves once published videos are analysed
- **t3** breakdown: newness 1.00, evidence_quality 0.73, practical_usefulness 0.25, business_value 0.25, educational_value 0.15, demonstrability 0.00, meaningful_result 0.00, audience_interest 0.50
  - notes: newest verified date 2026-09-24 (4 days); meaningful_result: judgement without justification counts as 0; audience interest: NO DATA yet (neutral 0.5) — improves once published videos are analysed

## TODAY'S SCREEN RECORDING

### Let a Gemini agent clean your messy CSV — AI Studio, then Python

- **Teaching item:** `tch_c187c188ff` (status RESEARCHED — you decide whether to record it)
- **Audience:** developers and technical operators; no-code builders for the first half
- **Problem:** cleaning and analysing files with an agent without building your own code-execution sandbox
- **What changed:** Google updated its managed agents (antigravity-preview-09-2026, Gemini 3.8 Flash) and added a Files API and a Credentials API.
- **Demo:** AI Studio Agents tab template -> attach a made-up messy CSV -> task -> watch the steps -> download the cleaned file; then the same from Python with a second request in the same sandbox
- **Value:** can_do: hand a Gemini managed agent a messy CSV and download a cleaned version from its sandbox, build: a small Python script that runs the agent on a file and asks follow-up questions in the same sandbox, mistake: avoid losing your files between requests by passing the stored environment id, understand: what a managed agent sandbox is and why your keys belong in the Credentials API, not the prompt

### Step-by-step recording plan

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

### Spoken script

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
- quality score 0.999 — **no blocking issues**

### Final takeaway

You can now hand a Gemini managed agent a file, let it do the work in its own sandbox, and pull the result back out, first in AI Studio and then from Python.

### Repurposing plan

| Format | Angle | Purpose | Audience |
|---|---|---|---|
| youtube_tutorial | the full 12-minute walkthrough with chapters | the complete lesson | people who want to do it |
| youtube_short | messy CSV in, clean CSV out, in one shot | show the result fast; point to the tutorial | scrollers curious about agents |
| tiktok | the environment-ID mistake and fix | one memorable lesson | developers |
| instagram_reel | before/after of the spreadsheet | visual proof | no-code builders |
| linkedin_post | what managed agents change for teams that process files | professional relevance | operators and team leads |
| x_post | the one detail that keeps your files between agent requests | single sharp tip | developers |
| x_thread | step-by-step of the Python flow | text version of the demo | developers |
| newsletter_section | why sandboxes matter and where to start | context and link | subscribers |
| blog_tutorial | written tutorial with the code and caveats | searchable reference | developers |
| carousel_concept | 5 steps from AI Studio to Python | save-able summary | LinkedIn readers |
| faq | questions about sandboxes, files, keys and cost | answer objections | all |
| checklist | before you give an agent your files | actionable safety and setup list | all |
| downloadable_resource | the fictional messy CSV + task prompt to practise with | hands-on practice | learners |
| course_lesson | lesson 1 of a managed-agents module | future course | course students |

## TODAY'S BUSINESS OPPORTUNITY

- **digital_product** — a practice pack (messy sample files, task prompts, a reusable Python script) directly supports the tutorial and costs little to test _Cheapest test:_ offer the free practice pack under the video and count downloads
- **automation_service** — small teams that clean the same exports every week could have that job moved to a managed agent run on a schedule _Cheapest test:_ ask in the video description who has a weekly export they clean by hand
- Not genuine here: course, workshop, consulting, implementation_service, saas, affiliate

## NEXT (your decision)

1. Review this brief. If you want to record it: `python -m aibos teaching select tch_c187c188ff --by <you>`
2. Build the full recording package: `python -m aibos record tch_c187c188ff`
3. After recording: `python -m aibos content-from-recording tch_c187c188ff --transcript <file>`

## EVIDENCE

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
| g9: The new harness uses 40% fewer output tokens on file changes. | PARTIALLY_SUPPORTED | 0.092 | s9 |
| g10: NokiaPowerUser reports the new harness capabilities are included within the standard free tier limits in Google AI Studio. | UNSUPPORTED | 0.03 | s5 |
| f1: Claude Fable 5.1 became available in Claude Code with a 1M-token context window. | SUPPORTED | 0.81 | s7, s6 |
| f2: Fable 5.1 defaults to High effort in Claude Code. | SUPPORTED | 0.729 | s6 |
| f3: When set to Low or Medium effort, Fable 5.1 achieves results similar to or better than Fable 5's at a much lower cost. | SUPPORTED | 0.729 | s6 |
| o1: OpenAI discontinued the Sora API on September 24, 2026. | SUPPORTED | 0.729 | s8 |
