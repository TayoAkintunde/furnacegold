ROLE FOCUS: {{focus}}

BRAND VOICE:
{{brand_voice}}

Write the spoken script for the recording plan. It should sound like a knowledgeable person sitting next to
the viewer: simple language, concrete examples, the real workflow, useful shortcuts, one honest mistake and
its correction, and the important caveats. Avoid exaggerated claims, fake urgency, motivational filler,
unnecessary jargon and AI hype. Define any technical term the first time it is spoken.
Numbers, model ids and commands must come from verified claims or sources.

Sections, in order, each with its plan step: hook, context, demo (several), teaching_moment, mistake,
proof, caveat, takeaway.

DATA schema:
{"scripts": [{"artifact_id": "{{agent_id}}-1", "opp_id": "t1", "platform": "script", "title": "...",
  "sections": [{"section": "hook", "step": 0, "text": "..."}],
  "text": "<all sections joined, in order>", "claim_ids": ["c1"], "source_ids": ["s1"],
  "value_statement": "After this video you can ..."}]}
