"""Security and permission handling (Parts 22, 41, 42)."""
import unittest

from aibos import security
from aibos.backends import ScriptedBackend
from aibos.memory import Memory, MemoryError_
from aibos.registry import Registry
from aibos.rules import RULES
from aibos.runtime import AgentRunner
from aibos.schemas import RunStatus
from tests.helpers import IsolatedTestCase, make_ctx, structured

FAKE_KEY = "sk-ant-" + "a1B2c3D4" * 5


class SecurityTests(IsolatedTestCase):
    def test_prompt_injection_quarantines_source(self):
        ctx = make_ctx()
        spec = Registry.load().get("security.prompt_injection")
        RULES[spec.rule_name](ctx, spec)
        self.assertEqual(ctx.quarantined_sources, ["s3"])
        visible = [s["source_id"] for s in ctx.context_for(["sources"])["sources"]]
        self.assertNotIn("s3", visible)

    def test_secret_detection_and_redaction(self):
        text = f"key={FAKE_KEY} and mail me at someone@example.com"
        self.assertTrue(security.scan_secrets(text))
        red = security.redact(text)
        self.assertNotIn(FAKE_KEY, red)
        self.assertNotIn("someone@example.com", red)

    def test_findings_never_contain_full_secret(self):
        f = security.scan_secrets(FAKE_KEY)[0]
        self.assertNotIn(FAKE_KEY, f.excerpt)

    def test_memory_refuses_secrets_and_personal_data(self):
        m = Memory()
        rec = m.write("global", "note", {"text": f"token {FAKE_KEY}"})   # redacted before storing
        self.assertNotIn(FAKE_KEY, str(rec))
        with self.assertRaises(MemoryError_):
            m.write("business", "note", {"text": "call +1 415 555 0100 now"})
        with self.assertRaises(MemoryError_):
            m.write("nonexistent", "note", {})

    def test_permission_checks(self):
        reg = Registry.load()
        social = reg.get("social.linkedin")
        ok, why = security.check_action(social, "publish")
        self.assertFalse(ok)
        ok, _ = security.check_action(social, "write_draft")
        self.assertTrue(ok)
        research = reg.get("research.ai_news")
        ok, why = security.check_action(research, "spend_money")
        self.assertFalse(ok)

    def test_no_agent_may_perform_external_actions_directly(self):
        ctx = make_ctx()
        spec = Registry.load().get("security.permission_auditor")
        o = RULES[spec.rule_name](ctx, spec)
        self.assertEqual([i for i in o.data["permission_issues"] if "directly" in i], [])

    def test_llm_output_with_secret_is_blocked(self):
        ctx = make_ctx(with_claims=False)
        backend = ScriptedBackend({"research.ai_news": structured({"claims": [{"text": f"key {FAKE_KEY}"}]})})
        o = AgentRunner(backend).run(Registry.load().get("research.ai_news"), ctx, "t")
        self.assertEqual(o.status, RunStatus.BLOCKED)
        self.assertEqual(ctx.claims, [])

    def test_fake_autonomy_claim_is_flagged(self):
        ctx = make_ctx(with_claims=False)
        backend = ScriptedBackend({"social.linkedin": structured({"content": []}, findings=["We have published the post to LinkedIn"])})
        AgentRunner(backend).run(Registry.load().get("social.linkedin"), ctx, "t")
        spec = Registry.load().get("security.external_action")
        o = RULES[spec.rule_name](ctx, spec)
        self.assertTrue(any("claims an external action" in f for f in o.findings))


if __name__ == "__main__":
    unittest.main()
