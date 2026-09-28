"""Agent communication contract, backends, budget and cache (Parts 26, 29, 43)."""
import unittest

from aibos.backends import OfflineBackend, ScriptedBackend, parse_json_object
from aibos.cost import Budget
from aibos.registry import Registry
from aibos.runtime import AgentRunner
from aibos.schemas import RunStatus
from tests.helpers import IsolatedTestCase, make_ctx, structured


class CommunicationTests(IsolatedTestCase):
    def setUp(self):
        super().setUp()
        self.reg = Registry.load()
        self.spec = self.reg.get("research.ai_news")

    def test_structured_output_parsed(self):
        ctx = make_ctx(with_claims=False)
        payload = structured({"claims": [{"text": "X", "kind": "FACT", "source_ids": ["s1"], "quotes": ["q"]}],
                              "findings": [{"development": "d"}]})
        o = AgentRunner(ScriptedBackend({"research.ai_news": payload}, "unit test")).run(self.spec, ctx, "t")
        self.assertEqual(o.status, RunStatus.OK)
        self.assertEqual(o.next_action, "next")
        self.assertEqual(o.provenance, "unit test")
        self.assertEqual(len(ctx.claims), 1)
        self.assertEqual(ctx.claims[0].verification.value, "UNVERIFIED")   # cannot self-certify
        self.assertEqual(ctx.board["findings"][0]["produced_by"], "research.ai_news")

    def test_contract_violation_degrades(self):
        ctx = make_ctx(with_claims=False)
        o = AgentRunner(ScriptedBackend({"research.ai_news": {"FINDINGS": ["only this"]}})).run(self.spec, ctx, "t")
        self.assertEqual(o.status, RunStatus.DEGRADED)
        self.assertTrue(any("contract violation" in e for e in o.errors))

    def test_undeclared_outputs_ignored(self):
        ctx = make_ctx(with_claims=False)
        o = AgentRunner(ScriptedBackend({"research.ai_news": structured({"content": [{"text": "sneaky"}]})})).run(self.spec, ctx, "t")
        self.assertNotIn("content", ctx.board)
        self.assertTrue(any("undeclared" in e for e in o.errors))

    def test_offline_backend_is_honest(self):
        ctx = make_ctx(with_claims=False)
        o = AgentRunner(OfflineBackend()).run(self.spec, ctx, "t")
        self.assertEqual(o.status, RunStatus.NO_MODEL)
        self.assertEqual(o.findings, [])
        self.assertTrue(o.errors)

    def test_missing_scripted_response_is_not_invented(self):
        ctx = make_ctx(with_claims=False)
        o = AgentRunner(ScriptedBackend({})).run(self.spec, ctx, "t")
        self.assertEqual(o.status, RunStatus.NO_MODEL)

    def test_low_confidence_escalates(self):
        ctx = make_ctx(with_claims=False)
        AgentRunner(ScriptedBackend({"research.ai_news": structured({}, confidence=0.2)})).run(self.spec, ctx, "t")
        self.assertTrue(any("below required" in e for e in ctx.escalations))

    def test_budget_exhaustion_skips_agent(self):
        ctx = make_ctx(with_claims=False)
        ctx.budget = Budget(max_units=1, max_llm_calls=10)
        o = AgentRunner(ScriptedBackend({"research.ai_news": structured({})})).run(self.spec, ctx, "t")
        self.assertEqual(o.status, RunStatus.SKIPPED)
        self.assertTrue(ctx.escalations)

    def test_disabled_agent_not_run(self):
        import dataclasses
        from aibos.schemas import AgentStatus
        spec = dataclasses.replace(self.spec, status=AgentStatus.DISABLED)
        o = AgentRunner(ScriptedBackend({"research.ai_news": structured({})})).run(spec, make_ctx(False), "t")
        self.assertEqual(o.status, RunStatus.SKIPPED)

    def test_parse_json_object(self):
        self.assertEqual(parse_json_object('text ```json\n{"a": 1}\n``` more'), {"a": 1})
        with self.assertRaises(ValueError):
            parse_json_object("no json here")


if __name__ == "__main__":
    unittest.main()
