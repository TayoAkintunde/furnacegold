ROLE FOCUS: {{focus}}

THE GUIDING QUESTION: "What important thing happened in AI recently that I can demonstrate and teach
people how to use?" — NOT "what AI news can I post today?". Do not favour a topic because it is popular.

For each verified development in the context, write one teaching opportunity. Use only verified claims
(verification = SUPPORTED) as facts; anything else is an assumption. If a development cannot be shown on
screen producing a real result, set demonstration.possible=false and give reject_reason.

Judgements (1-5) MUST each include a justification grounded in the claims; an unjustified score counts as 0.
Value answers must be specific to this topic (what exactly the viewer can do/solve/build/understand/avoid).

DATA schema:
{"teaching_opportunities": [{
  "opp_id": "t1", "topic": "...", "trend": "...", "category": "<one of the focus areas>", "claim_ids": ["c1"],
  "what_changed": "...", "why_it_matters": "...", "who_should_care": "...", "what_can_do": "...",
  "demonstration": {"possible": true, "how": "...", "setup": ["..."], "accounts": ["..."], "cost": "..."},
  "problem_solved": "...", "what_to_build": "...", "beginner_mistakes": ["..."],
  "simplest_example": "...", "advanced_example": "...", "what_makes_valuable": "...",
  "teaching_angle": "...", "difficulty": "beginner|intermediate|advanced",
  "value_answers": {"can_do": "...", "problem": "...", "build": "...", "understand": "...", "mistake": "..."},
  "judgements": {"practical_usefulness": {"score": 4, "justification": "..."},
                 "educational_value": {"score": 4, "justification": "..."},
                 "demonstrability": {"score": 4, "justification": "..."},
                 "meaningful_result": {"score": 4, "justification": "..."},
                 "business_value": {"score": 3, "justification": "..."}},
  "reject_reason": null}]}
