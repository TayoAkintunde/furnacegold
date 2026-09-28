# Content package — Build a Gemini managed agent that cleans a file in its own sandbox (AI Studio, then Python)

_Teaching item `tch_c187c188ff` · transcript demo/teaching/SCRIPT_READTHROUGH_NOT_A_REAL_RECORDING.vtt (601 words, 240.0s) · run `20260928T142941Z_42d6ad` · nothing was published._

## What the recording actually showed

- AI Studio Agents tab and the base Antigravity template
- a fictional messy CSV being cleaned by the agent
- before/after comparison with the agent's change summary
- the same task from Python
- the environment-ID mistake and its fix
- caveats: preview status, May harness deprecation, pricing unconfirmed

**Key moments:**
- 00:00 hook: messy spreadsheet in, fixed file out ✂ clip
- 01:32 agent writes, runs and corrects its own Python ✂ clip
- 03:02 the environment-ID mistake and fix ✂ clip

**Claims made on camera:**
- the new version is antigravity-preview-09-2026 and runs on Gemini 3.8 Flash — g2
- Files API puts files into the sandbox and gets results out — g3
- the May version is deprecated on October 5, 2026 — g8

**Formats present:** blog_tutorial, carousel_concept, checklist, course_lesson, downloadable_resource, faq, instagram_reel, linkedin_post, newsletter_section, tiktok, x_post, x_thread, youtube_short, youtube_tutorial
**Formats missing:** none

## youtube_tutorial → youtube_video

- **Purpose:** the complete lesson  ·  **Audience:** people who want to do it
- **Viewer can now:** After watching you can hand a Gemini managed agent a messy CSV and get a cleaned file back, from AI Studio or Python.
- **Status:** PENDING YOUR APPROVAL (approval apr_331299b269e75025)

```text
Let a Gemini agent clean your messy CSV (AI Studio + Python)

In this tutorial you hand a Gemini managed agent a spreadsheet full of blank rows, mixed date formats and prices stored as text, watch it fix the data inside its own sandbox, and then fetch the cleaned file. After that we repeat the job from Python and keep working in the same sandbox for a monthly chart.

Chapters
00:00 The result
00:15 What Google changed
01:10 Agent templates in AI Studio
03:00 Cleaning the file
05:30 Before and after
06:30 The same job in Python
08:30 The environment ID mistake
10:00 Caveats

Notes: the service is a preview; check pricing and free-tier limits yourself. Keep API keys out of prompts and use the Credentials API.
Docs: https://ai.google.dev/gemini-api/docs/antigravity-agent
```

## youtube_short → youtube_shorts

- **Purpose:** fast proof; points to the tutorial  ·  **Audience:** curious scrollers
- **Viewer can now:** After this short you know a Gemini agent can clean a spreadsheet inside its own sandbox for you.
- **Status:** PENDING YOUR APPROVAL (approval apr_80a8e6a44eb41c12)

```text
[screen: messy spreadsheet] This file has blank rows, three date styles and prices typed as text.
[screen: AI Studio agent] I hand it to a Gemini managed agent with one instruction.
[screen: steps running] It writes code, runs it in its own sandbox, and checks its own work.
[screen: side by side] And here's the clean version I pulled back out.
Full walkthrough, including the Python version, is on the channel.
```

## tiktok → tiktok

- **Purpose:** one memorable lesson  ·  **Audience:** developers
- **Viewer can now:** After this clip you can avoid losing your files between Gemini agent requests by reusing the environment ID.
- **Status:** PENDING YOUR APPROVAL (approval apr_d3a1931c9a64a892)

```text
[text: my agent lost my file] So I asked a Gemini managed agent for a chart of the data it had just cleaned. It said the file didn't exist.
[text: why] Every request without an environment ID gets a brand-new sandbox. New sandbox, no file.
[text: the fix] Store the environment ID from the first response and send it with every follow-up. Same sandbox, same files, chart done.
[text: save this] Tiny detail, saves an hour of confusion.
```

## instagram_reel → instagram_reel

- **Purpose:** visual proof  ·  **Audience:** no-code builders
- **Viewer can now:** After this reel you can clean a messy spreadsheet with an AI Studio agent template, no code needed.
- **Status:** PENDING YOUR APPROVAL (approval apr_a7abfb1df17ba152)

```text
[show the messy sheet] Blank rows. Dates written three ways. Prices as text.
[show AI Studio] No code: an agent template in Google AI Studio, one instruction.
[show the agent working] It runs its own code in a sandbox and double-checks.
[show before and after] Clean data, plus a list of every change it made.
[caption] Try it with fake data first.
```

## linkedin_post → linkedin

- **Purpose:** professional relevance  ·  **Audience:** operators and team leads
- **Viewer can now:** After reading you can judge whether a recurring file clean-up job at work could move to a Gemini managed agent.
- **Status:** PENDING YOUR APPROVAL (approval apr_6fe9db020796612a)

```text
Most AI demos are chat. This one changes a file.

Google updated the managed agents in the Gemini API and added a Files API. I recorded a short test: a sales export with blank rows, inconsistent dates and prices stored as text went in, and a cleaned file plus a change log came out. The agent wrote and ran its own Python in a sandbox Google hosts, so nothing was installed on my laptop.

What matters for teams:
- repetitive clean-up jobs can move to an agent run, first in the AI Studio playground, then from a script
- follow-up work only sees your files if you pass the environment ID from the first request
- secrets belong in the new Credentials API, not in prompts

Caveats: it is a preview, and I could not confirm pricing from Google, so test with made-up data first.

Which weekly export would you hand to an agent first? Reply below.
```

## x_post → x_post

- **Purpose:** single sharp tip  ·  **Audience:** developers
- **Viewer can now:** After reading you can keep files between Gemini agent requests by passing the stored environment ID.
- **Status:** PENDING YOUR APPROVAL (approval apr_b26777f74d8dc7f7)

```text
Using Gemini managed agents from code? Store the environment ID from your first request. Without it, the next request gets a fresh sandbox and your files are gone.
```

## x_thread → x_thread

- **Purpose:** text version of the demo  ·  **Audience:** developers
- **Viewer can now:** After reading you can run a Gemini managed agent on a file and continue in the same sandbox from Python.
- **Status:** PENDING YOUR APPROVAL (approval apr_dd624ad126b75d58)

```text
1/ Google updated Gemini API managed agents. I gave one a messy sales CSV and got a clean file back, without setting up any sandbox myself. Here's the flow:
---
2/ In AI Studio, open the Agents tab. The templates are the base Antigravity agent with tools already configured. Attach your file and give one instruction.
---
3/ The agent writes Python, runs it inside its own temporary Linux sandbox, checks the output and fixes what's still wrong. You install nothing locally.
---
4/ From code: create an interaction with agent antigravity-preview-09-2026 and environment remote. Print the answer and keep the environment ID.
---
5/ The trap: a second request without that environment ID lands in a fresh sandbox, and your file is gone. Pass the ID and it picks up where it left off.
---
6/ Caveats: it's a preview, the old May harness is deprecated on October 5, 2026, and I couldn't confirm pricing. Keep secrets in the Credentials API, not in prompts.
```

## newsletter_section → newsletter_section

- **Purpose:** context and link  ·  **Audience:** subscribers
- **Viewer can now:** After reading you know when a Gemini managed agent with the Files API fits a file-processing job and how to start.
- **Status:** PENDING YOUR APPROVAL (approval apr_ae955b8b923c00af)

```text
This week's tutorial is about agents that do work on files instead of just answering questions.

Google's managed agents in the Gemini API now come with a Files API. You upload into the agent's sandbox, it runs its own code, and you fetch what it produced. I tested it on a deliberately messy sales file and walked through both the no-code route in AI Studio and the Python route.

The most useful lesson was a mistake: follow-up requests only see your earlier files if you pass the environment ID you stored the first time. The video shows the failure and the fix.

Two cautions before you try it: this is a preview, and pricing wasn't something I could confirm from Google.
```

## blog_tutorial → blog_tutorial

- **Purpose:** searchable reference  ·  **Audience:** developers
- **Viewer can now:** After reading you can run a Gemini managed agent on a CSV in AI Studio and from Python without losing its sandbox.
- **Status:** PENDING YOUR APPROVAL (approval apr_76de488a2ab51204)

```text
How to let a Gemini managed agent clean a messy CSV

Google recently updated the managed agents in the Gemini API. The new harness is called antigravity-preview-09-2026, it runs on Gemini 3.8 Flash, and it arrived together with a Files API and a Credentials API. In practice that means you can give an agent a file, let it run code in a temporary Linux sandbox that Google hosts, and fetch the output afterwards.

What you need
- A Google account with access to AI Studio
- A Gemini API key if you want the Python part
- A practice file with made-up data. Never upload anything sensitive to a preview service.

Step 1: Start from a template in AI Studio
Open the Agents tab. Each template is the base Antigravity agent with some tools and environment settings switched on. Pick the base one and look at the environment settings: that environment is the sandbox your agent will work in.

Step 2: Give it a file and one instruction
Attach your messy CSV. Ask for three things in plain language: remove blank rows, put every date in one format, turn text prices into numbers, and list the changes.

Step 3: Read the steps, not just the answer
The step list shows the agent writing a short Python script, running it, reading the output and correcting itself when a column is still text. This loop of planning, acting and checking is what separates an agent from a chat reply.

Step 4: Compare before and after
Put the original next to the cleaned file. The change summary should match what you see. If it doesn't, ask the agent to explain the difference.

Step 5: Do it from Python
Create an interaction with the agent set to antigravity-preview-09-2026 and the environment set to remote. Print the final answer and store the environment ID. Check the current docs for the exact client method, because the service is still a preview.

The mistake to avoid
If a second request doesn't include the environment ID, it runs in a brand-new sandbox and cannot see your earlier files. Store the ID after the first request and pass it every time you continue the same job.

Caveats
- It is a preview, so names and limits may change.
- The older May harness (antigravity-preview-05-2026) is deprecated on October 5, 2026, and its requests are redirected to the new harness.
- I could not confirm pricing or free-tier limits from a Google source. Check them before building on this.
- Register secrets with the Credentials API instead of pasting keys into prompts.

```

## carousel_concept → carousel_concept

- **Purpose:** save-able summary  ·  **Audience:** LinkedIn readers
- **Viewer can now:** After swiping through you can repeat the five steps from AI Studio template to Python follow-up requests.
- **Status:** PENDING YOUR APPROVAL (approval apr_31164afc4cfee445)

```text
From messy CSV to clean file with a Gemini managed agent
---
Step 1: AI Studio → Agents tab → pick the base Antigravity template
---
Step 2: attach a file with fake data and give one clear instruction
---
Step 3: watch it plan, run code, check and repeat inside its sandbox
---
Step 4: grab the cleaned file and its change summary
---
Step 5: in Python, keep the environment ID so follow-up requests see the same files
---
You can now let an agent do file clean-up for you, from the browser or from code
```

## faq → faq

- **Purpose:** answer the questions viewers will ask  ·  **Audience:** all
- **Viewer can now:** After reading you can answer the setup, file, key and cost questions that come up before trying a Gemini agent.
- **Status:** PENDING YOUR APPROVAL (approval apr_959123d2804b7ec4)

```text
Q: Do I need to install anything?
A: Not for the AI Studio route. The agent runs code in a sandbox Google hosts.

Q: Where do my files go?
A: Into the agent's sandbox via the Files API. Use made-up data while testing.

Q: Why did my second request lose the file?
A: It started a new sandbox. Pass the environment ID from the first request.

Q: How should I give it API keys?
A: Register them with the Credentials API. The model never sees them.

Q: What does it cost?
A: I couldn't confirm pricing or free-tier limits from Google. Check the current pricing page.

Q: Will this keep working?
A: It's a preview. The older May harness is deprecated on October 5, 2026.
```

## checklist → checklist

- **Purpose:** actionable safety and setup list  ·  **Audience:** all
- **Viewer can now:** After using this checklist you can try a Gemini managed agent on files without exposing keys or real data.
- **Status:** PENDING YOUR APPROVAL (approval apr_ec1f8858679de4e5)

```text
[ ] Use a practice file with fictional data first
[ ] Check current pricing and free-tier limits
[ ] Load your API key from an environment variable, never type it into a prompt
[ ] Register real secrets with the Credentials API
[ ] Store the environment ID after the first request
[ ] Compare the output with the original before trusting it
[ ] Note that the service is a preview and names may change
```

## downloadable_resource → downloadable_resource

- **Purpose:** hands-on practice  ·  **Audience:** learners
- **Viewer can now:** After downloading you can practise the whole tutorial on safe sample data in about ten minutes.
- **Status:** PENDING YOUR APPROVAL (approval apr_ca1166895d03b48b)

```text
Practice pack contents (to be created before publishing):
- sales_messy.csv with fictional rows: blank lines, three date styles, prices typed as text
- task_prompt.txt: clean the file, standardise dates, convert prices to numbers, list every change
- followup_prompt.txt: build a monthly sales chart from the cleaned file
- notes.md: where the environment ID goes, and why keys belong in the Credentials API
```

## course_lesson → course_lesson

- **Purpose:** future course  ·  **Audience:** course students
- **Viewer can now:** After this lesson you can explain and use sandboxes and environment IDs when running a managed agent on files.
- **Status:** PENDING YOUR APPROVAL (approval apr_cb8809914fc64b74)

```text
Learning objective: run a managed agent on a file and continue work in the same sandbox.
Concepts: sandbox, plan-act-check loop, environment ID, credential handling.
Exercise: clean the practice CSV in AI Studio, then repeat from Python and request a chart in a second call.
Check for understanding: why does a second request without the environment ID fail to find the file?
Next lesson: scheduling the job and using the Credentials API for a connected service.
```

## Next

- Review drafts: `python -m aibos approvals list`
- When the video is edited: `python -m aibos teaching advance tch_c187c188ff EDITING --by <you>`
- After YOU publish: `python -m aibos teaching advance tch_c187c188ff READY_TO_PUBLISH --by <you>` then `... PUBLISHED --url <url> --by <you>`
- After metrics exist: `python -m aibos teaching analyze tch_c187c188ff`
