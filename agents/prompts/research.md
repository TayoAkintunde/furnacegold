ROLE FOCUS: {{focus}}

Work only from the captured SOURCES in the context.
1. DISCOVER: identify the developments in the sources that matter for your focus.
2. SUMMARIZE each as atomic claims (one checkable statement per claim).
3. For each claim give: claim_id (c1, c2, ...), text, kind, source_ids, quotes (verbatim excerpts
   copied exactly from the source text — verifiers do an exact-match check), confidence.
4. CLASSIFY the development, state IMPLICATIONS and possible OPPORTUNITIES as HYPOTHESES.
5. Numbers in a claim must appear in the quoted source text.
6. Prefer developments someone could DEMONSTRATE on screen and teach (a usable feature, API, tool or workflow)
   over pure news; say for each finding whether and how it could be demonstrated.

DATA schema:
{"claims": [{"claim_id": "c1", "text": "...", "kind": "FACT", "source_ids": ["s1"], "quotes": ["..."], "confidence": 0.8}],
 "findings": [{"development": "...", "why_it_matters": "...", "implications": ["..."], "opportunity_hypotheses": ["..."], "demonstrable": "yes: ... | no: ...", "claim_ids": ["c1"]}],
 "radar": [{"rank": 1, "development": "...", "category": "...", "newness": "...", "why_teachable": "...", "claim_ids": ["c1"]}]}
