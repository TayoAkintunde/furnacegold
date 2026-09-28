"""Builds the scripted agent outputs for the /teach-today, /record and /content-from-recording example.

These outputs were AUTHORED BY THE CLAUDE CODE SESSION OPERATOR acting as the model backend (no Anthropic
API key in the build environment). They use only demo/teaching/sources.json. Every deterministic check
(verification, scoring, gates, script/plan/package quality) runs for real on them.

Run:  python demo/teaching/build_responses.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROV = ("scripted: authored 2026-09-28 by the Claude Code session operator acting as the model backend "
        "(no Anthropic API key in this environment); grounded only in demo/teaching/sources.json")


def S(data, findings, uncertainties=(), assumptions=(), recommendations=(), next_action="", confidence=0.8, sources=()):
    return {"TASK": "see stage", "FINDINGS": list(findings), "EVIDENCE": [], "ASSUMPTIONS": list(assumptions),
            "UNCERTAINTIES": list(uncertainties), "RECOMMENDATIONS": list(recommendations),
            "NEXT_ACTION": next_action, "CONFIDENCE": confidence, "SOURCES": list(sources), "DATA": data}


# ------------------------------------------------------------------ research: claims + radar
CLAIMS = [
    {"claim_id": "g1", "text": "Google released the antigravity-preview-09-2026 managed-agent harness, which replaces antigravity-preview-05-2026.",
     "kind": "FACT", "source_ids": ["s1"], "quotes": ["The antigravity-preview-09-2026 version was released and replaces the previous antigravity-preview-05-2026"]},
    {"claim_id": "g2", "text": "The updated harness runs on Gemini 3.8 Flash, with the model configurable per interaction.",
     "kind": "FACT", "source_ids": ["s2", "s4"], "quotes": ["runs on Gemini 3.8 Flash with the model configurable per interaction", "defaulting to Gemini 3.8 Flash"]},
    {"claim_id": "g3", "text": "A new Files API lets you upload into a running sandbox, list what the agent wrote, and download the files you need.",
     "kind": "FACT", "source_ids": ["s2", "s4"], "quotes": ["You can upload into a running sandbox, list what the agent wrote, and download the files you need", "The Files API adds a dedicated file-context surface for agent workflows"]},
    {"claim_id": "g4", "text": "A new Credentials API lets you register secrets once and attach them to an MCP server or a sandbox environment variable without the model seeing them.",
     "kind": "FACT", "source_ids": ["s2"], "quotes": ["You can register secrets once and attach them to an MCP server or a sandbox environment variable, and the model never sees them"]},
    {"claim_id": "g5", "text": "Google AI Studio's playground and Agents-tab templates let you prototype managed agents without writing API calls.",
     "kind": "FACT", "source_ids": ["s3"], "quotes": ["Google AI Studio Playground provides a visual interface to prototype and learn how to build managed agents without having to create and write API calls", "The Agents tab has a series of templates that pre-configure the base Antigravity Agent"]},
    {"claim_id": "g6", "text": "Each call can provision a Linux sandbox where the agent can run Bash, Python and Node.js commands, install packages and run tests.",
     "kind": "FACT", "source_ids": ["s1"], "quotes": ["Each call can provision a Linux sandbox and starts a tool-use loop", "The agent can run Bash, Python, and Node.js commands, install packages, run tests"]},
    {"claim_id": "g7", "text": "From code, you create an interaction with the agent set to antigravity-preview-09-2026 and the environment set to remote, and store interaction.environment_id to keep using the same sandbox.",
     "kind": "FACT", "source_ids": ["s1"], "quotes": ["create an interaction with the agent \"antigravity-preview-09-2026\", pass input text, and set environment to \"remote\"", "You should store interaction.id and interaction.environment_id to continue the conversation in the same sandbox"]},
    {"claim_id": "g8", "text": "antigravity-preview-05-2026 will be deprecated on October 5, 2026, after which requests to it are redirected to the updated harness.",
     "kind": "FACT", "source_ids": ["s2"], "quotes": ["antigravity-preview-05-2026 will be deprecated on October 5, 2026, after which requests to it are redirected to the updated harness"]},
    {"claim_id": "g9", "text": "The new harness uses 40% fewer output tokens on file changes.",
     "kind": "FACT", "source_ids": ["s9"], "quotes": ["The new harness uses 40% fewer output tokens on file changes"]},
    {"claim_id": "g10", "text": "NokiaPowerUser reports the new harness capabilities are included within the standard free tier limits in Google AI Studio.",
     "kind": "OBSERVATION", "source_ids": ["s5"], "quotes": ["Google has included access to these new harness capabilities within the standard free tier limits in Google AI Studio"]},
    {"claim_id": "f1", "text": "Claude Fable 5.1 became available in Claude Code with a 1M-token context window.",
     "kind": "FACT", "source_ids": ["s7", "s6"], "quotes": ["Claude Fable 5.1 became available in Claude Code with a 1M-token context window", "Fable 5.1 supports a 1 million token context window"]},
    {"claim_id": "f2", "text": "Fable 5.1 defaults to High effort in Claude Code.",
     "kind": "FACT", "source_ids": ["s6"], "quotes": ["Fable 5.1 defaults to High effort in Claude Code"]},
    {"claim_id": "f3", "text": "When set to Low or Medium effort, Fable 5.1 achieves results similar to or better than Fable 5's at a much lower cost.",
     "kind": "FACT", "source_ids": ["s6"], "quotes": ["When set to Low or Medium effort, Fable 5.1 achieves results similar to or better than Fable 5's at a much lower cost"]},
    {"claim_id": "o1", "text": "OpenAI discontinued the Sora API on September 24, 2026.",
     "kind": "FACT", "source_ids": ["s8"], "quotes": ["The Sora API will be discontinued on September 24, 2026"]},
]

RADAR = [
    {"rank": 1, "development": "Gemini API managed agents: updated Antigravity harness (antigravity-preview-09-2026) plus new Files and Credentials APIs",
     "category": "AI agents", "newness": "covered by AICoder on 2026-09-19", "why_teachable": "usable today in AI Studio and from Python; a real task can be run and its output file downloaded on screen",
     "claim_ids": ["g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8"]},
    {"rank": 2, "development": "Claude Fable 5.1 available in Claude Code (1M context, effort levels)",
     "category": "Claude / Claude Code", "newness": "Claude Code week 36 (Aug 31 – Sep 4)", "why_teachable": "effort levels can be compared on one real coding task",
     "claim_ids": ["f1", "f2", "f3"]},
    {"rank": 3, "development": "Sora API shut down", "category": "AI models", "newness": "September 24, 2026",
     "why_teachable": "important news, but there is nothing left to demonstrate", "claim_ids": ["o1"]}]

research = S({"claims": CLAIMS, "radar": RADAR, "findings": [
    {"development": r["development"], "why_it_matters": r["why_teachable"], "demonstrable": "yes" if r["rank"] < 3 else "no: the API is gone",
     "claim_ids": r["claim_ids"]} for r in RADAR]},
    ["Three candidate developments from the captured sources; the Gemini managed-agents update is the most demonstrable."],
    uncertainties=["Only search-engine extracts were available, not full pages.",
                   "s3 says the original Antigravity agent was built on Gemini 3.5 Flash; the September update (s2, s4) says 3.8 Flash. Claims use the update.",
                   "Performance and free-tier statements come from an unattributed digest (s9) and a blog (s5); they are recorded but not relied on."],
    sources=["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9"])

# ------------------------------------------------------------------ teaching opportunities
def J(u, e, d, r, b, why):
    return {"practical_usefulness": {"score": u, "justification": why["u"]}, "educational_value": {"score": e, "justification": why["e"]},
            "demonstrability": {"score": d, "justification": why["d"]}, "meaningful_result": {"score": r, "justification": why["r"]},
            "business_value": {"score": b, "justification": why["b"]}}

T1 = {"opp_id": "t1", "topic": "Build a Gemini managed agent that cleans a file in its own sandbox (AI Studio, then Python)",
      "trend": "Gemini API managed agents: antigravity-preview-09-2026 harness + Files API + Credentials API", "category": "AI agents",
      "claim_ids": ["g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8"],
      "what_changed": "Google updated its managed agents (antigravity-preview-09-2026, Gemini 3.8 Flash) and added a Files API and a Credentials API.",
      "why_it_matters": "You can now hand an agent a real file, let it run code in its own sandbox, and get the result back, without building the sandbox yourself.",
      "who_should_care": "developers and technical operators who want an agent to process files, and no-code builders prototyping in AI Studio",
      "what_can_do": "give an agent a file, have it clean or analyse the data with code in a sandbox, and download the output",
      "demonstration": {"possible": True, "how": "AI Studio Agents tab template -> attach a made-up messy CSV -> task -> watch the steps -> download the cleaned file; then the same from Python with a second request in the same sandbox",
                        "setup": ["Google account with AI Studio access", "Gemini API key for the Python part", "a fictional messy CSV"],
                        "accounts": ["Google AI Studio"], "cost": "check current pricing and free-tier limits before recording (not confirmed by a Google source)"},
      "problem_solved": "cleaning and analysing files with an agent without setting up your own code-execution sandbox",
      "what_to_build": "an agent run that turns a messy sales CSV into a cleaned file plus a summary of changes, reusable from Python",
      "beginner_mistakes": ["not storing the environment id, so the second request starts a new sandbox and the file is gone",
                            "pasting real API keys into the prompt instead of using the Credentials API",
                            "uploading sensitive data into a preview service"],
      "simplest_example": "AI Studio template + one CSV + one instruction + download the result",
      "advanced_example": "a Python job that uploads a daily export, runs the agent, reuses the same environment for follow-up analysis, and uses the Credentials API for a connected service",
      "what_makes_valuable": "the viewer sees a real file go in and a better file come out, and gets the one detail (environment id) that makes multi-step work possible",
      "teaching_angle": "show the agent doing real work on a real file, not a chat demo", "difficulty": "beginner",
      "value_answers": {"can_do": "hand a Gemini managed agent a messy CSV and download a cleaned version from its sandbox",
                        "build": "a small Python script that runs the agent on a file and asks follow-up questions in the same sandbox",
                        "mistake": "avoid losing your files between requests by passing the stored environment id",
                        "understand": "what a managed agent sandbox is and why your keys belong in the Credentials API, not the prompt"},
      "judgements": J(4, 5, 5, 5, 4, {"u": "file cleaning and analysis is a common everyday task and g3/g6 make it possible without your own sandbox",
                                      "e": "teaches sandboxes, the plan-act-check loop, environment ids and credential handling in one workflow",
                                      "d": "every step happens in AI Studio and a terminal, with a before-and-after file as visible proof",
                                      "r": "the viewer ends with a cleaned file, a change summary and a reusable Python script",
                                      "b": "file-processing agents are a plausible automation-service and template offer for small teams"}),
      "reject_reason": None}

T2 = {"opp_id": "t2", "topic": "Choose the right effort level for Claude Fable 5.1 in Claude Code on one real task",
      "trend": "Claude Fable 5.1 in Claude Code", "category": "Claude / Claude Code", "claim_ids": ["f1", "f2", "f3"],
      "what_changed": "Claude Fable 5.1 is available in Claude Code with a 1M-token context window and defaults to High effort.",
      "why_it_matters": "Lower effort can give similar results at much lower cost, so the default may not be the right choice for every task.",
      "who_should_care": "developers using Claude Code daily", "what_can_do": "compare effort levels on their own task and pick a sensible default",
      "demonstration": {"possible": True, "how": "run the same bug-fix task at Low and High effort and compare the diffs, time and cost",
                        "setup": ["Claude Code with Fable 5.1 access", "a small repo with a known bug"], "accounts": ["Claude plan or API"], "cost": "uses paid model calls"},
      "problem_solved": "overspending on effort for routine tasks", "what_to_build": "a personal rule of thumb for effort per task type",
      "beginner_mistakes": ["judging effort levels on a single tiny task"], "simplest_example": "one bug fix at two effort levels",
      "advanced_example": "a small benchmark of five of your own tasks across effort levels",
      "what_makes_valuable": "a side-by-side on the viewer's kind of work",
      "teaching_angle": "measure before you change your defaults", "difficulty": "intermediate",
      "value_answers": {"can_do": "compare Fable 5.1 effort levels on their own coding task and choose a default",
                        "mistake": "avoid paying for High effort on routine tasks without checking whether Low is enough"},
      "judgements": J(4, 4, 3, 3, 3, {"u": "effort choice affects cost on every Claude Code session according to f3",
                                      "e": "teaches how to evaluate a model setting on your own work",
                                      "d": "demonstrable, but results vary run to run so one recording proves little",
                                      "r": "the result is a judgement call rather than a built artefact",
                                      "b": "some consulting value for teams choosing defaults, but thin on its own"}),
      "reject_reason": None}

T3 = {"opp_id": "t3", "topic": "What the Sora API shutdown means", "trend": "Sora API shut down", "category": "AI models",
      "claim_ids": ["o1"], "what_changed": "OpenAI discontinued the Sora API on September 24, 2026.",
      "why_it_matters": "products built on it lost a feature", "who_should_care": "teams that used Sora",
      "what_can_do": "nothing new can be done with the Sora API", "demonstration": {"possible": False, "how": ""},
      "problem_solved": "", "what_to_build": "", "beginner_mistakes": [], "simplest_example": "", "advanced_example": "",
      "what_makes_valuable": "", "teaching_angle": "news", "difficulty": "beginner",
      "value_answers": {"understand": "understand the Sora shutdown news"},
      "judgements": J(2, 2, 1, 1, 2, {"u": "the API no longer exists so there is little to use",
                                      "e": "news explainer only, no hands-on skill", "d": "nothing can be shown working",
                                      "r": "no result to produce", "b": "no genuine offer from this topic"}),
      "reject_reason": "important news, but there is nothing to demonstrate; not a screen-recording topic"}

opps = S({"teaching_opportunities": [T1, T2, T3]},
         ["t1 (Gemini managed agents + Files API) is the most demonstrable and useful; t2 is a solid runner-up; t3 is news, not a tutorial."],
         uncertainties=["Audience interest is unknown: the business profile is not configured and no videos have been analysed yet."],
         assumptions=["Viewers have or can create a Google account for AI Studio."], confidence=0.75)

# ------------------------------------------------------------------ recording plan
PLAN = {"opp_id": "t1", "title": "Let a Gemini agent clean your messy CSV — AI Studio, then Python",
        "audience": "developers and technical operators; no-code builders for the first half",
        "problem": "cleaning and analysing files with an agent without building your own code-execution sandbox",
        "hook": {"text": "In the next ten minutes you'll give a Gemini agent a messy spreadsheet, let it clean the data in its own sandbox, and download the fixed file.", "seconds": 11},
        "context": "Google updated the managed agents in the Gemini API (antigravity-preview-09-2026, on Gemini 3.8 Flash) and added a Files API and a Credentials API. A managed agent is one Google runs for you: it plans, runs code, checks the result and repeats until the task is done.",
        "prerequisites": ["Google account with AI Studio access", "Gemini API key (for the Python part)",
                          "Python with the Google GenAI client installed", "sales_messy.csv — a made-up file with blank rows, mixed date formats and prices typed as text"],
        "verify_before_recording": ["current pricing and free-tier limits for managed agents (only a blog claims free-tier access)",
                                    "exact Python client method name for creating an interaction (the docs extract only says 'create an interaction')",
                                    "where the file-attach control is in the AI Studio Agents playground",
                                    "that antigravity-preview-09-2026 is still the current agent id on recording day"],
        "demonstration": [
            {"step": 1, "on_screen": "Google AI Studio home, then click the Agents tab and scroll the template list", "say": "These templates are the base Antigravity agent with tools and settings pre-configured.", "why": "orient beginners before any code"},
            {"step": 2, "on_screen": "Open the base Antigravity agent template and show its tool and environment settings", "say": "This is where the agent's sandbox and tools are configured.", "why": "makes the sandbox concrete"},
            {"step": 3, "on_screen": "Open sales_messy.csv in a spreadsheet: blank rows, three date formats, prices as text", "say": "Here's our starting point, a file I made up for this video.", "why": "starting state for the before/after proof"},
            {"step": 4, "on_screen": "Attach sales_messy.csv to the agent and type the task: clean it, standardise dates, convert prices, summarise the changes", "say": "One file, one instruction.", "why": "the simplest useful example"},
            {"step": 5, "on_screen": "Watch the agent's steps: it writes Python, runs it, reads the output and corrects itself", "say": "Plan, act, check, repeat.", "why": "teaching moment: the agent loop"},
            {"step": 6, "on_screen": "Download the cleaned file and the change summary; open both next to the original", "say": "Same data, fixed.", "why": "proof"},
            {"step": 7, "on_screen": "Terminal: a short Python script that creates an interaction with agent antigravity-preview-09-2026, environment remote, then prints `interaction.output_text` and `interaction.environment_id`; the client call shown as `client.interactions.create()`", "say": "Now the same thing from code.", "why": "moves the viewer from playground to something they can automate"},
            {"step": 8, "on_screen": "Second request asking for a monthly sales chart: first without the environment id (file not found), then with it (chart created)", "say": "This is the mistake almost everyone makes.", "why": "mistake and correction; teaches environment ids"},
            {"step": 9, "on_screen": "Slide with the limitations and the Credentials API note", "say": "A few honest caveats.", "why": "limitations"}],
        "teaching_moments": [{"at_step": 2, "explain": "what a sandbox is: a temporary Linux machine that exists only for this agent's task"},
                             {"at_step": 5, "explain": "the plan-act-check loop, and why the agent can fix its own errors"},
                             {"at_step": 8, "explain": "interaction id vs environment id: the environment id is what keeps your files between requests"},
                             {"at_step": 9, "explain": "why secrets go in the Credentials API, never in the prompt"}],
        "proof": "The original CSV and the downloaded cleaned CSV side by side, plus the agent's written summary of every change, and the chart from the second request.",
        "variation": "Reuse the same environment for a second request, a monthly sales chart built from the cleaned file.",
        "limitations": ["preview service: names and limits can change",
                        "antigravity-preview-05-2026 is deprecated on October 5, 2026 (requests redirect to the new harness)",
                        "pricing and free-tier limits not confirmed from a Google source",
                        "do not upload sensitive data to a preview service"],
        "takeaway": "You can now hand a Gemini managed agent a file, let it do the work in its own sandbox, and pull the result back out, first in AI Studio and then from Python.",
        "estimated_recording_minutes": 12, "difficulty": "beginner", "claim_ids": ["g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8"]}

SECTIONS = [
    ("hook", 0, "In the next ten minutes you'll give a Gemini agent a messy spreadsheet, let it clean the data in its own sandbox, and download the fixed file."),
    ("context", 0, "Here's what changed. Google updated the managed agents in the Gemini API. The new version is called antigravity-preview-09-2026, it replaces the May version, and it runs on Gemini 3.8 Flash. Two new pieces matter for us. A Files API, so you can put files into the agent's sandbox and get results back out. And a Credentials API, so the agent can use your services without the model ever seeing your keys. A managed agent just means Google runs the agent for you. You send a task, and it plans, runs code, checks the result and keeps going until it's done."),
    ("demo", 1, "Let's start in Google AI Studio. I'm opening the Agents tab. You can see a list of templates here. They're the base Antigravity agent with some tools and settings already switched on."),
    ("demo", 2, "I'll open the base template. This panel is where the tools and the environment are set. The environment is the sandbox: think of it as a temporary Linux computer that exists only for this task."),
    ("demo", 3, "This is our starting point. It's a sales file I made up for this video. There are blank rows, dates written three different ways, and some prices typed as text. Nothing real in here, and that matters, because whatever you upload goes into the sandbox."),
    ("demo", 4, "I attach the file and give it one instruction: clean this file, make every date the same format, turn the prices into numbers, and tell me what you changed."),
    ("teaching_moment", 5, "Now watch the steps while it works. It wrote a small Python script, ran it, read the output, noticed one column was still text, and fixed it. That loop is the whole idea: plan, act, check, repeat. You didn't install anything on your machine."),
    ("proof", 6, "And here's the result. On the left, the original file with the gaps and the mixed dates. On the right, the cleaned file I just downloaded from the sandbox, and underneath, the agent's summary of every change it made."),
    ("demo", 7, "Now the same thing from code, because that's how you'd use this for real. You create an interaction, set the agent to antigravity-preview-09-2026, pass your input, and set the environment to remote. Then you print the final answer and the environment ID. Check the current docs for the exact client call, because this is still a preview."),
    ("mistake", 8, "Now I'll ask for a chart of monthly sales. And it can't find the file. That's my mistake, and it's the one almost everyone makes. I didn't pass the environment ID, so this request started a brand-new sandbox, and my file isn't in it. The docs say to store the interaction ID and the environment ID. So I pass the environment ID and run it again. There's the chart, built from the same cleaned file."),
    ("caveat", 9, "A few honest caveats. This is a preview, so names and limits can change. If you built on the older May version, it's deprecated on October 5, 2026, and requests get redirected to the new one. I haven't confirmed pricing or free-tier limits from Google, so check those before you rely on this. And never paste real keys into a prompt. That's exactly what the Credentials API is for."),
    ("takeaway", 9, "So now you can hand a Gemini managed agent a file, let it do the work in its own sandbox, and pull the result back out, first in AI Studio and then from Python. Try it on a messy file of your own, and keep that environment ID."),
]
SCRIPT = {"artifact_id": "teaching.script_writer-1", "opp_id": "t1", "platform": "script", "title": PLAN["title"],
          "sections": [{"section": s, "step": n, "text": t} for s, n, t in SECTIONS],
          "text": "\n\n".join(t for _, _, t in SECTIONS), "claim_ids": PLAN["claim_ids"], "source_ids": ["s1", "s2", "s3", "s4"],
          "value_statement": "After this video you can hand a Gemini managed agent a messy CSV and download a cleaned file from its sandbox."}

REPURPOSE_PLAN = [
    {"format": "youtube_tutorial", "angle": "the full 12-minute walkthrough with chapters", "purpose": "the complete lesson", "audience": "people who want to do it"},
    {"format": "youtube_short", "angle": "messy CSV in, clean CSV out, in one shot", "purpose": "show the result fast; point to the tutorial", "audience": "scrollers curious about agents"},
    {"format": "tiktok", "angle": "the environment-ID mistake and fix", "purpose": "one memorable lesson", "audience": "developers"},
    {"format": "instagram_reel", "angle": "before/after of the spreadsheet", "purpose": "visual proof", "audience": "no-code builders"},
    {"format": "linkedin_post", "angle": "what managed agents change for teams that process files", "purpose": "professional relevance", "audience": "operators and team leads"},
    {"format": "x_post", "angle": "the one detail that keeps your files between agent requests", "purpose": "single sharp tip", "audience": "developers"},
    {"format": "x_thread", "angle": "step-by-step of the Python flow", "purpose": "text version of the demo", "audience": "developers"},
    {"format": "newsletter_section", "angle": "why sandboxes matter and where to start", "purpose": "context and link", "audience": "subscribers"},
    {"format": "blog_tutorial", "angle": "written tutorial with the code and caveats", "purpose": "searchable reference", "audience": "developers"},
    {"format": "carousel_concept", "angle": "5 steps from AI Studio to Python", "purpose": "save-able summary", "audience": "LinkedIn readers"},
    {"format": "faq", "angle": "questions about sandboxes, files, keys and cost", "purpose": "answer objections", "audience": "all"},
    {"format": "checklist", "angle": "before you give an agent your files", "purpose": "actionable safety and setup list", "audience": "all"},
    {"format": "downloadable_resource", "angle": "the fictional messy CSV + task prompt to practise with", "purpose": "hands-on practice", "audience": "learners"},
    {"format": "course_lesson", "angle": "lesson 1 of a managed-agents module", "purpose": "future course", "audience": "course students"}]

BUSINESS = [
    {"type": "digital_product", "genuine": True, "reasoning": "a practice pack (messy sample files, task prompts, a reusable Python script) directly supports the tutorial and costs little to test",
     "evidence_claim_ids": ["g3", "g6", "g7"], "assumptions": ["viewers want ready-made practice material"], "cheapest_test": "offer the free practice pack under the video and count downloads"},
    {"type": "automation_service", "genuine": True, "reasoning": "small teams that clean the same exports every week could have that job moved to a managed agent run on a schedule",
     "evidence_claim_ids": ["g3", "g6"], "assumptions": ["teams have repetitive file-cleaning work", "they will trust a preview service"], "cheapest_test": "ask in the video description who has a weekly export they clean by hand"},
    {"type": "course", "genuine": False, "reasoning": "one tutorial is not a course yet; revisit after the beginner/intermediate/advanced videos show demand"},
    {"type": "workshop", "genuine": False, "reasoning": "too early; no audience data"},
    {"type": "consulting", "genuine": False, "reasoning": "no evidence yet that anyone would pay for advice on this specific tool"},
    {"type": "implementation_service", "genuine": False, "reasoning": "overlaps with the automation service; do not split before any demand is seen"},
    {"type": "saas", "genuine": False, "reasoning": "Google already provides the managed runtime; a thin wrapper has little defensible value"},
    {"type": "affiliate", "genuine": False, "reasoning": "no affiliate programme identified in the sources"}]

teach_today = {
    "research.trend_radar": research,
    "teaching.opportunity_analyst": opps,
    "teaching.recording_planner": S({"recording_plans": [PLAN]}, ["Plan for t1: 9 on-screen steps, 4 teaching moments, before/after proof."],
                                    uncertainties=PLAN["verify_before_recording"]),
    "teaching.script_writer": S({"scripts": [SCRIPT]}, ["Spoken script with a real mistake-and-fix moment (environment id) and caveats."]),
    "teaching.repurposer": S({"content": [], "repurposing_plan": REPURPOSE_PLAN},
                             ["Repurposing plan only; the package is written from the real recording via /content-from-recording."]),
    "teaching.business_analyst": S({"teaching_business": BUSINESS}, ["Two genuine, low-cost opportunities; the rest are not forced."],
                                   uncertainties=["No audience or revenue data exists yet."], confidence=0.6),
}

# ------------------------------------------------------------------ /record
LEVELS = [
    {"level": "beginner", "title": "What is a Gemini managed agent? Clean a CSV in AI Studio (no code)", "question": "What is this and how do I use it?",
     "promise": "Use an AI Studio agent template to clean a file and download the result.", "demo": "steps 1-6 of the plan, no Python",
     "outcome": "a cleaned CSV and a plain-English idea of what a sandbox is", "prerequisites": ["Google account"], "est_minutes": 7,
     "value_statement": "After this you can use an AI Studio agent template to clean a messy CSV without writing code.", "claim_ids": ["g5", "g3"]},
    {"level": "intermediate", "title": "Automate a weekly file clean-up with the Gemini Interactions API", "question": "How can I use this to solve a real problem?",
     "promise": "Script the same job in Python and keep working in one sandbox across requests.", "demo": "steps 7-8, plus a second file",
     "outcome": "a reusable Python script that uploads, cleans, charts and downloads", "prerequisites": ["Gemini API key", "Python basics"], "est_minutes": 12,
     "value_statement": "After this you can run a managed agent from Python and reuse its sandbox with the environment id.", "claim_ids": ["g7", "g3", "g6"]},
    {"level": "advanced", "title": "A production-shaped file agent: Files API, Credentials API and scheduled runs", "question": "How can I build a serious workflow/system with this?",
     "promise": "Design a scheduled job that feeds exports to the agent, stores results, and uses registered credentials for a connected service.",
     "demo": "architecture sketch, credential registration, a scheduled run, failure handling", "outcome": "a runnable design with secrets kept out of prompts",
     "prerequisites": ["the intermediate lesson", "a scheduler (cron or similar)"], "est_minutes": 20,
     "value_statement": "After this you can design a scheduled file-processing agent that keeps secrets out of the prompt using the Credentials API.", "claim_ids": ["g4", "g3", "g7"]}]

PRODUCTION = {"opp_id": "t1",
              "setup_checklist": ["Close unrelated tabs and notifications", "Sign in to AI Studio before recording",
                                  "Create sales_messy.csv (fictional data only)", "Prepare the Python script in an editor, with the key loaded from an environment variable, never on screen",
                                  "Zoom the browser and terminal to a readable size"],
              "accounts_and_costs": ["Google AI Studio account", "Gemini API key — check current pricing and free-tier limits before recording"],
              "test_data": ["sales_messy.csv: about forty rows, blank rows, three date formats, prices with currency symbols as text"],
              "shot_list": [{"shot": 1, "on_screen": "face or title card with the before/after spreadsheet", "duration_s": 12},
                            {"shot": 2, "on_screen": "AI Studio Agents tab and template settings", "duration_s": 60},
                            {"shot": 3, "on_screen": "messy CSV, attach, task prompt", "duration_s": 60},
                            {"shot": 4, "on_screen": "agent steps running", "duration_s": 90},
                            {"shot": 5, "on_screen": "before/after side by side", "duration_s": 45},
                            {"shot": 6, "on_screen": "Python script and output", "duration_s": 120},
                            {"shot": 7, "on_screen": "environment-id mistake and fix", "duration_s": 90},
                            {"shot": 8, "on_screen": "caveats slide", "duration_s": 45}],
              "callouts": ["Sandbox = temporary Linux machine for this task", "Store the environment ID", "Keys go in the Credentials API, not the prompt", "Preview: check pricing"],
              "chapters": [{"time": "00:00", "title": "The result"}, {"time": "00:15", "title": "What changed"}, {"time": "01:10", "title": "AI Studio agent templates"},
                           {"time": "03:00", "title": "Cleaning the file"}, {"time": "05:30", "title": "Before and after"}, {"time": "06:30", "title": "Same thing in Python"},
                           {"time": "08:30", "title": "The environment ID mistake"}, {"time": "10:00", "title": "Caveats"}],
              "title_options": ["Let a Gemini agent clean your messy CSV (AI Studio + Python)", "Gemini managed agents: give it a file, get a better file back",
                                "The one setting that keeps your files between Gemini agent requests"],
              "thumbnail_text_options": ["MESSY CSV → CLEAN", "Agent does the cleanup", "Don't lose your files"],
              "description": "Google updated Gemini API managed agents (antigravity-preview-09-2026) and added a Files API and a Credentials API. In this tutorial you give an agent a messy spreadsheet in AI Studio, watch it clean the data in its own sandbox, download the result, then do the same from Python and keep working in the same sandbox with the environment ID. Caveats: preview service; check pricing and free-tier limits; never paste keys into prompts.",
              "resources": ["https://ai.google.dev/gemini-api/docs/antigravity-agent", "https://aistudio.google.com/learn/managed-agents-updated-harness-files-credentials",
                            "practice pack: sales_messy.csv + task prompt (to be created)"]}

record = {
    "teaching.level_designer": S({"teaching_levels": LEVELS}, ["Three distinct lessons from one discovery."]),
    "teaching.production_planner": S({"production": [PRODUCTION]}, ["Setup, shot list, chapters, titles, description, resources."],
                                     uncertainties=["Pricing and free-tier limits must be checked before recording."]),
}

if __name__ == "__main__":
    for name, d in (("teach_today_responses.json", teach_today), ("record_responses.json", record)):
        (HERE / name).write_text(json.dumps({"provenance": PROV, "responses": d}, indent=1, ensure_ascii=False))
        print("wrote", name)


# ------------------------------------------------------------------ /content-from-recording (on a script READ-THROUGH)
def readthrough_vtt() -> str:
    """Timed read-through of the generated script at 150 wpm. NOT a real recording."""
    lines = ["WEBVTT", "",
             "NOTE This is a timed read-through of the GENERATED SCRIPT, made to demonstrate /content-from-recording.",
             "NOTE It is NOT a transcript of a real screen recording.", ""]
    t = 0.0

    def ts(x):
        return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{x % 60:06.3f}"
    for i, (_, _, text) in enumerate(SECTIONS, 1):
        dur = len(text.split()) / 2.5
        lines += [str(i), f"{ts(t)} --> {ts(t + dur)}", text, ""]
        t += dur
    return "\n".join(lines)


THREAD = "\n---\n".join([
    "1/ Google updated Gemini API managed agents. I gave one a messy sales CSV and got a clean file back, without setting up any sandbox myself. Here's the flow:",
    "2/ In AI Studio, open the Agents tab. The templates are the base Antigravity agent with tools already configured. Attach your file and give one instruction.",
    "3/ The agent writes Python, runs it inside its own temporary Linux sandbox, checks the output and fixes what's still wrong. You install nothing locally.",
    "4/ From code: create an interaction with agent antigravity-preview-09-2026 and environment remote. Print the answer and keep the environment ID.",
    "5/ The trap: a second request without that environment ID lands in a fresh sandbox, and your file is gone. Pass the ID and it picks up where it left off.",
    "6/ Caveats: it's a preview, the old May harness is deprecated on October 5, 2026, and I couldn't confirm pricing. Keep secrets in the Credentials API, not in prompts.",
])

CAROUSEL = "\n---\n".join([
    "From messy CSV to clean file with a Gemini managed agent",
    "Step 1: AI Studio → Agents tab → pick the base Antigravity template",
    "Step 2: attach a file with fake data and give one clear instruction",
    "Step 3: watch it plan, run code, check and repeat inside its sandbox",
    "Step 4: grab the cleaned file and its change summary",
    "Step 5: in Python, keep the environment ID so follow-up requests see the same files",
    "You can now let an agent do file clean-up for you, from the browser or from code",
])

BLOG = """How to let a Gemini managed agent clean a messy CSV

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
"""

PACKAGE = [
    ("youtube_tutorial", "youtube_video", "Let a Gemini agent clean your messy CSV (AI Studio + Python)", "the complete lesson", "people who want to do it",
     "Let a Gemini agent clean your messy CSV (AI Studio + Python)\n\nIn this tutorial you hand a Gemini managed agent a spreadsheet full of blank rows, mixed date formats and prices stored as text, watch it fix the data inside its own sandbox, and then fetch the cleaned file. After that we repeat the job from Python and keep working in the same sandbox for a monthly chart.\n\nChapters\n00:00 The result\n00:15 What Google changed\n01:10 Agent templates in AI Studio\n03:00 Cleaning the file\n05:30 Before and after\n06:30 The same job in Python\n08:30 The environment ID mistake\n10:00 Caveats\n\nNotes: the service is a preview; check pricing and free-tier limits yourself. Keep API keys out of prompts and use the Credentials API.\nDocs: https://ai.google.dev/gemini-api/docs/antigravity-agent",
     "After watching you can hand a Gemini managed agent a messy CSV and get a cleaned file back, from AI Studio or Python."),
    ("youtube_short", "youtube_shorts", "Messy CSV in, clean CSV out", "fast proof; points to the tutorial", "curious scrollers",
     "[screen: messy spreadsheet] This file has blank rows, three date styles and prices typed as text.\n[screen: AI Studio agent] I hand it to a Gemini managed agent with one instruction.\n[screen: steps running] It writes code, runs it in its own sandbox, and checks its own work.\n[screen: side by side] And here's the clean version I pulled back out.\nFull walkthrough, including the Python version, is on the channel.",
     "After this short you know a Gemini agent can clean a spreadsheet inside its own sandbox for you."),
    ("tiktok", "tiktok", "The environment ID trap", "one memorable lesson", "developers",
     "[text: my agent lost my file] So I asked a Gemini managed agent for a chart of the data it had just cleaned. It said the file didn't exist.\n[text: why] Every request without an environment ID gets a brand-new sandbox. New sandbox, no file.\n[text: the fix] Store the environment ID from the first response and send it with every follow-up. Same sandbox, same files, chart done.\n[text: save this] Tiny detail, saves an hour of confusion.",
     "After this clip you can avoid losing your files between Gemini agent requests by reusing the environment ID."),
    ("instagram_reel", "instagram_reel", "Before and after: an agent cleans my spreadsheet", "visual proof", "no-code builders",
     "[show the messy sheet] Blank rows. Dates written three ways. Prices as text.\n[show AI Studio] No code: an agent template in Google AI Studio, one instruction.\n[show the agent working] It runs its own code in a sandbox and double-checks.\n[show before and after] Clean data, plus a list of every change it made.\n[caption] Try it with fake data first.",
     "After this reel you can clean a messy spreadsheet with an AI Studio agent template, no code needed."),
    ("linkedin_post", "linkedin", "Agents that work on files, not just chat", "professional relevance", "operators and team leads",
     "Most AI demos are chat. This one changes a file.\n\nGoogle updated the managed agents in the Gemini API and added a Files API. I recorded a short test: a sales export with blank rows, inconsistent dates and prices stored as text went in, and a cleaned file plus a change log came out. The agent wrote and ran its own Python in a sandbox Google hosts, so nothing was installed on my laptop.\n\nWhat matters for teams:\n- repetitive clean-up jobs can move to an agent run, first in the AI Studio playground, then from a script\n- follow-up work only sees your files if you pass the environment ID from the first request\n- secrets belong in the new Credentials API, not in prompts\n\nCaveats: it is a preview, and I could not confirm pricing from Google, so test with made-up data first.\n\nWhich weekly export would you hand to an agent first? Reply below.",
     "After reading you can judge whether a recurring file clean-up job at work could move to a Gemini managed agent."),
    ("x_post", "x_post", "One detail for Gemini managed agents", "single sharp tip", "developers",
     "Using Gemini managed agents from code? Store the environment ID from your first request. Without it, the next request gets a fresh sandbox and your files are gone.",
     "After reading you can keep files between Gemini agent requests by passing the stored environment ID."),
    ("x_thread", "x_thread", "Gemini managed agents, file in and file out", "text version of the demo", "developers", THREAD,
     "After reading you can run a Gemini managed agent on a file and continue in the same sandbox from Python."),
    ("newsletter_section", "newsletter_section", "This week: an agent that edits files", "context and link", "subscribers",
     "This week's tutorial is about agents that do work on files instead of just answering questions.\n\nGoogle's managed agents in the Gemini API now come with a Files API. You upload into the agent's sandbox, it runs its own code, and you fetch what it produced. I tested it on a deliberately messy sales file and walked through both the no-code route in AI Studio and the Python route.\n\nThe most useful lesson was a mistake: follow-up requests only see your earlier files if you pass the environment ID you stored the first time. The video shows the failure and the fix.\n\nTwo cautions before you try it: this is a preview, and pricing wasn't something I could confirm from Google.",
     "After reading you know when a Gemini managed agent with the Files API fits a file-processing job and how to start."),
    ("blog_tutorial", "blog_tutorial", "How to let a Gemini managed agent clean a messy CSV", "searchable reference", "developers", BLOG,
     "After reading you can run a Gemini managed agent on a CSV in AI Studio and from Python without losing its sandbox."),
    ("carousel_concept", "carousel_concept", "From messy CSV to clean file", "save-able summary", "LinkedIn readers", CAROUSEL,
     "After swiping through you can repeat the five steps from AI Studio template to Python follow-up requests."),
    ("faq", "faq", "Gemini managed agents: common questions", "answer the questions viewers will ask", "all",
     "Q: Do I need to install anything?\nA: Not for the AI Studio route. The agent runs code in a sandbox Google hosts.\n\nQ: Where do my files go?\nA: Into the agent's sandbox via the Files API. Use made-up data while testing.\n\nQ: Why did my second request lose the file?\nA: It started a new sandbox. Pass the environment ID from the first request.\n\nQ: How should I give it API keys?\nA: Register them with the Credentials API. The model never sees them.\n\nQ: What does it cost?\nA: I couldn't confirm pricing or free-tier limits from Google. Check the current pricing page.\n\nQ: Will this keep working?\nA: It's a preview. The older May harness is deprecated on October 5, 2026.",
     "After reading you can answer the setup, file, key and cost questions that come up before trying a Gemini agent."),
    ("checklist", "checklist", "Before you give an agent your files", "actionable safety and setup list", "all",
     "[ ] Use a practice file with fictional data first\n[ ] Check current pricing and free-tier limits\n[ ] Load your API key from an environment variable, never type it into a prompt\n[ ] Register real secrets with the Credentials API\n[ ] Store the environment ID after the first request\n[ ] Compare the output with the original before trusting it\n[ ] Note that the service is a preview and names may change",
     "After using this checklist you can try a Gemini managed agent on files without exposing keys or real data."),
    ("downloadable_resource", "downloadable_resource", "Practice pack: messy CSV + task prompt", "hands-on practice", "learners",
     "Practice pack contents (to be created before publishing):\n- sales_messy.csv with fictional rows: blank lines, three date styles, prices typed as text\n- task_prompt.txt: clean the file, standardise dates, convert prices to numbers, list every change\n- followup_prompt.txt: build a monthly sales chart from the cleaned file\n- notes.md: where the environment ID goes, and why keys belong in the Credentials API",
     "After downloading you can practise the whole tutorial on safe sample data in about ten minutes."),
    ("course_lesson", "course_lesson", "Module: managed agents, lesson one", "future course", "course students",
     "Learning objective: run a managed agent on a file and continue work in the same sandbox.\nConcepts: sandbox, plan-act-check loop, environment ID, credential handling.\nExercise: clean the practice CSV in AI Studio, then repeat from Python and request a chart in a second call.\nCheck for understanding: why does a second request without the environment ID fail to find the file?\nNext lesson: scheduling the job and using the Credentials API for a connected service.",
     "After this lesson you can explain and use sandboxes and environment IDs when running a managed agent on files."),
]

TRANSCRIPT_ANALYSIS = {"what_was_shown": ["AI Studio Agents tab and the base Antigravity template", "a fictional messy CSV being cleaned by the agent",
                                           "before/after comparison with the agent's change summary", "the same task from Python",
                                           "the environment-ID mistake and its fix", "caveats: preview status, May harness deprecation, pricing unconfirmed"],
                       "key_moments": [{"time": "00:00", "description": "hook: messy spreadsheet in, fixed file out", "clip_candidate": True},
                                       {"time": "01:32", "description": "agent writes, runs and corrects its own Python", "clip_candidate": True},
                                       {"time": "03:02", "description": "the environment-ID mistake and fix", "clip_candidate": True}],
                       "claims_made": [{"text": "the new version is antigravity-preview-09-2026 and runs on Gemini 3.8 Flash", "claim_id": "g2"},
                                       {"text": "Files API puts files into the sandbox and gets results out", "claim_id": "g3"},
                                       {"text": "the May version is deprecated on October 5, 2026", "claim_id": "g8"}],
                       "questions_answered": ["what is a managed agent", "why the second request lost the file"],
                       "mistakes_shown": ["missing environment ID on the follow-up request"],
                       "differences_from_plan": ["this is a script read-through, so nothing was actually shown on screen"]}

content = {
    "teaching.transcript_analyst": S({"transcript_analysis": [TRANSCRIPT_ANALYSIS]},
                                     ["Transcript analysed; it is a read-through of the script, not a recording."],
                                     uncertainties=["No real screen footage exists; clip timestamps are from the read-through timing."]),
    "teaching.repurposer": S({"content": [{"artifact_id": f"pkg-{f}", "format": f, "platform": p, "title": t, "purpose": pu,
                                           "audience": au, "text": tx, "value_statement": v, "claim_ids": ["g2", "g3", "g7", "g8"],
                                           "source_ids": ["s1", "s2"]} for f, p, t, pu, au, tx, v in PACKAGE], "repurposing_plan": []},
                             ["14 formats, each adapted to its platform and purpose."]),
}

if __name__ == "__main__":
    (HERE / "content_responses.json").write_text(json.dumps({"provenance": PROV, "responses": content}, indent=1, ensure_ascii=False))
    (HERE / "SCRIPT_READTHROUGH_NOT_A_REAL_RECORDING.vtt").write_text(readthrough_vtt())
    print("wrote content_responses.json and SCRIPT_READTHROUGH_NOT_A_REAL_RECORDING.vtt")
