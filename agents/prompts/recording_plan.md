ROLE FOCUS: {{focus}}

Plan a screen recording for the selected teaching opportunity (teaching_selection). Be literal about what
appears on screen. Only use verified claims as facts; any product detail you are unsure of goes into
"verify_before_recording". Numbers, model ids and commands must come from the claims or sources.

Structure: HOOK (5-15 seconds; states the result or the problem solved) -> CONTEXT (what it is, why care) ->
DEMONSTRATION (open the tool, starting state, what we will build, perform the workflow, explain decisions,
show the result, a useful variation, limitations) -> TEACHING MOMENTS -> PROOF -> TAKEAWAY.

DATA schema:
{"recording_plans": [{
  "opp_id": "t1", "title": "...", "audience": "...", "problem": "...",
  "hook": {"text": "...", "seconds": 10}, "context": "...",
  "prerequisites": ["..."], "verify_before_recording": ["..."],
  "demonstration": [{"step": 1, "on_screen": "...", "say": "...", "why": "..."}],
  "teaching_moments": [{"at_step": 3, "explain": "..."}],
  "proof": "...", "variation": "...", "limitations": ["..."], "takeaway": "...",
  "estimated_recording_minutes": 12, "difficulty": "beginner|intermediate|advanced", "claim_ids": ["c1"]}]}
