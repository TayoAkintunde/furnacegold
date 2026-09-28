"""Scripted (fictional) agent outputs for the teaching pipeline tests. ExampleAI / Widget-1 are invented."""
from tests.helpers import claims_raw, structured

JUDGED = {"practical_usefulness": {"score": 4, "justification": "builders can switch a real workflow to Widget-1 today"},
          "educational_value": {"score": 4, "justification": "shows how to evaluate a model before switching"},
          "demonstrability": {"score": 5, "justification": "every step happens in a browser and terminal on screen"},
          "meaningful_result": {"score": 4, "justification": "viewer ends with a working side-by-side evaluation"},
          "business_value": {"score": 3, "justification": "evaluation setups are a common consulting request"}}

GOOD = {"opp_id": "t1", "topic": "Evaluate Widget-1 against your current model on your own tasks", "trend": "Widget-1 release",
        "category": "AI models", "claim_ids": ["c1"], "what_changed": "ExampleAI released Widget-1",
        "why_it_matters": "a new model is only useful if it beats yours on your tasks", "who_should_care": "builders",
        "what_can_do": "run a side-by-side evaluation", "problem_solved": "choosing a model without guessing",
        "demonstration": {"possible": True, "how": "run the same prompts through both models and compare",
                          "setup": ["API key"], "accounts": ["ExampleAI"], "cost": "check before recording"},
        "what_to_build": "a small evaluation script with a scored results table",
        "beginner_mistakes": ["trusting the benchmark instead of your own tasks"],
        "simplest_example": "five prompts, two models, one table", "advanced_example": "automated nightly evaluation",
        "what_makes_valuable": "the viewer leaves with a reusable evaluation", "teaching_angle": "test before you switch",
        "difficulty": "beginner",
        "value_answers": {"can_do": "run a side-by-side evaluation of two models on their own prompts",
                          "mistake": "avoid switching models because of a benchmark score alone"},
        "judgements": JUDGED, "reject_reason": None}

NOT_DEMO = dict(GOOD, opp_id="t2", topic="ExampleAI raises a new funding round",
                demonstration={"possible": False, "how": ""}, reject_reason="funding news cannot be demonstrated")

WEAK = dict(GOOD, opp_id="t3", topic="Widget-1 is the best model ever made", claim_ids=["c3"],
            value_answers={"understand": "learn about ai"})

PLAN = {"opp_id": "t1", "title": "Test Widget-1 on your own prompts in 10 minutes", "audience": "builders",
        "problem": "choosing a model without guessing",
        "hook": {"text": "Before you switch to Widget-1, run this ten-minute test on your own prompts.", "seconds": 6},
        "context": "ExampleAI released Widget-1, and it scores 87.5% on the Example benchmark.",
        "prerequisites": ["ExampleAI account", "Python installed"], "verify_before_recording": ["current pricing page"],
        "demonstration": [
            {"step": 1, "on_screen": "Open the terminal in an empty project folder", "say": "we start from nothing", "why": "reproducible"},
            {"step": 2, "on_screen": "Create prompts.txt with five of your real prompts", "say": "use real work", "why": "your tasks"},
            {"step": 3, "on_screen": "Run compare.py against both models", "say": "same prompts, two models", "why": "fair test"},
            {"step": 4, "on_screen": "Open results.csv in a spreadsheet and score each answer", "say": "you judge", "why": "your criteria"},
            {"step": 5, "on_screen": "Sort by score and show the winner per prompt", "say": "here is the answer", "why": "proof"}],
        "teaching_moments": [{"at_step": 2, "explain": "why your own prompts beat a benchmark"}],
        "proof": "The results table shows which model won on each of the five prompts.",
        "variation": "run it nightly", "limitations": ["five prompts is a small sample"],
        "takeaway": "You can now test any new model on your own work before switching.",
        "estimated_recording_minutes": 10, "difficulty": "beginner", "claim_ids": ["c1"]}

SCRIPT = {"artifact_id": "teaching.script_writer-1", "opp_id": "t1", "platform": "script",
          "title": "Test Widget-1 on your own prompts",
          "sections": [
              {"section": "hook", "step": 0, "text": "Before you switch to Widget-1, run this ten-minute test on your own prompts."},
              {"section": "context", "step": 0, "text": "ExampleAI released Widget-1, and it scores 87.5% on the Example benchmark. That tells you how it does on their test, not on yours."},
              {"section": "demo", "step": 2, "text": "So you open a file, and you paste five prompts you actually used this week."},
              {"section": "mistake", "step": 3, "text": "Oops, I ran it with the old model twice. You can see both columns match. Let me fix the model name and run it again."},
              {"section": "proof", "step": 5, "text": "Now you sort by score, and you can see which model won each prompt."},
              {"section": "caveat", "step": 5, "text": "Five prompts is a small sample, so treat this as a first signal."},
              {"section": "takeaway", "step": 5, "text": "You can now test any new model on your own work before you switch."}],
          "claim_ids": ["c1"], "source_ids": ["s1"],
          "value_statement": "After this video you can test a new model on your own prompts before switching."}
SCRIPT["text"] = " ".join(s["text"] for s in SCRIPT["sections"])

PKG_TEXT = {
    "youtube_tutorial": ("youtube_video", "Test Widget-1 on your own prompts. Chapters: 00:00 why benchmarks are not enough, 01:10 set up prompts.txt, 03:00 run the comparison, 06:30 read the results table. You will leave with a reusable way to decide whether a new model is worth switching to, based on your own work rather than a leaderboard."),
    "x_post": ("x_post", "Widget-1 scores 87.5% on the Example benchmark. That is their test, not yours. I ran five of my real prompts through both models instead."),
    "linkedin_post": ("linkedin", "A new model came out this month. Before switching anything, I recorded a short test: five real prompts, two models, one results table. The benchmark said 87.5%. My own prompts told a more useful story about which tasks improved and which did not. The method takes ten minutes and works for any model release."),
}


def package(n_formats: int = 3) -> list[dict]:
    return [{"artifact_id": f"pkg-{fmt}", "format": fmt, "platform": plat, "title": fmt, "purpose": "teach the test",
             "audience": "builders", "text": text, "claim_ids": ["c1"], "source_ids": ["s1"],
             "value_statement": "After this you can test a new model on your own prompts before switching."}
            for fmt, (plat, text) in list(PKG_TEXT.items())[:n_formats]]


TRANSCRIPT = """1
00:00:00,000 --> 00:00:06,000
Before you switch to Widget-1, run this test on your own prompts.

2
00:00:06,000 --> 00:00:20,000
Widget-1 scores 87.5% on the Example benchmark. That is their test, not yours.

3
00:00:20,000 --> 00:01:30,000
I paste five prompts I used this week and run both models. Oops, same model twice. Fixed.
"""


def teach_today_responses() -> dict:
    return {
        "research.trend_radar": structured({"claims": claims_raw(), "findings": [{"development": "Widget-1 release", "claim_ids": ["c1"]}],
                                            "radar": [{"rank": 1, "development": "Widget-1 release", "category": "AI models",
                                                       "why_teachable": "can be tested on screen", "claim_ids": ["c1"]}]}),
        "teaching.opportunity_analyst": structured({"teaching_opportunities": [GOOD, NOT_DEMO, WEAK]}),
        "teaching.recording_planner": structured({"recording_plans": [PLAN]}),
        "teaching.script_writer": structured({"scripts": [SCRIPT]}),
        "teaching.repurposer": structured({"content": [], "repurposing_plan": [
            {"format": "youtube_short", "angle": "the 87.5% vs my prompts moment", "purpose": "hook to full video", "audience": "builders"}]}),
        "teaching.business_analyst": structured({"teaching_business": [
            {"type": "consulting", "genuine": True, "reasoning": "teams ask for evaluation setups", "cheapest_test": "offer 3 audits"},
            {"type": "saas", "genuine": False, "reasoning": "too thin for software"}]}),
    }


def record_responses() -> dict:
    return {
        "teaching.level_designer": structured({"teaching_levels": [
            {"level": lv, "title": f"{lv} lesson", "question": "q", "promise": "p", "demo": "d", "outcome": "o",
             "est_minutes": 10, "value_statement": "After this you can test a new model on your own prompts."}
            for lv in ("beginner", "intermediate", "advanced")]}),
        "teaching.production_planner": structured({"production": [{"opp_id": "t1", "setup_checklist": ["clean desktop"],
                                                                    "shot_list": [{"shot": 1, "on_screen": "terminal", "duration_s": 30}],
                                                                    "chapters": [{"time": "00:00", "title": "Why"}],
                                                                    "title_options": ["Test Widget-1 on your own prompts"],
                                                                    "description": "d", "resources": ["results template"]}]}),
    }


def content_responses() -> dict:
    return {
        "teaching.transcript_analyst": structured({"transcript_analysis": [{"what_was_shown": ["side-by-side test"],
                                                                            "key_moments": [{"time": "00:06", "description": "87.5% claim", "clip_candidate": True}],
                                                                            "claims_made": [{"text": "87.5% on the Example benchmark", "claim_id": "c1"}]}]}),
        "teaching.repurposer": structured({"content": package(3), "repurposing_plan": []}),
    }
