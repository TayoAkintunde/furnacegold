"""Content generation quality gates (Parts 9, 41: content generation)."""
import unittest

from aibos.evidence import aggregate_verification
from aibos.orchestrator import Hooks
from aibos.registry import Registry
from aibos.rules import RULES
from aibos.rules.content_quality import flesch
from aibos.selection import PlanStep
from tests.helpers import IsolatedTestCase, make_ctx


class ContentQualityTests(IsolatedTestCase):
    def setUp(self):
        super().setUp()
        self.reg = Registry.load()
        self.ctx = make_ctx(with_content=True)
        for aid in ("verification.citation", "verification.primary_source", "verification.statistics"):
            spec = self.reg.get(aid)
            o = RULES[spec.rule_name](self.ctx, spec)
            self.ctx.merge("verification_reports", o.data["verification_reports"], aid)
        aggregate_verification(self.ctx.claims, self.ctx.board["verification_reports"], self.ctx.sources)
        for spec in self.reg.by_family("content_quality"):
            o = RULES[spec.rule_name](self.ctx, spec)
            self.ctx.merge("quality_reports", o.data["quality_reports"], spec.agent_id)
        Hooks.quality_gate(self.ctx, PlanStep("QUALITY", "orch.quality", [], ""))
        self.gate = self.ctx.board["quality_gate"]

    def test_good_draft_passes(self):
        g = self.gate["good-linkedin"]
        self.assertEqual(g["blocking"], [], g)
        self.assertGreater(g["score"], 0.7)

    def test_bad_draft_blocked_for_expected_reasons(self):
        blocking = " | ".join(self.gate["bad-x"]["blocking"])
        for expected in ("platform_fit", "hype", "clickbait", "factuality", "hallucination", "cta"):
            self.assertIn(expected, blocking)
        bad = next(a for a in self.ctx.board["content"] if a["artifact_id"] == "bad-x")
        self.assertTrue(bad["blocked"])

    def test_ai_slop_and_hype_warn(self):
        g = self.gate["bad-x"]
        issues = " | ".join(g["warnings"] + g["blocking"])
        self.assertIn("ai_slop", issues)
        self.assertIn("hype words", issues)

    def test_readability_formula(self):
        easy, _ = flesch("The cat sat on the mat. It was a sunny day.")
        hard, _ = flesch("Notwithstanding considerable organizational heterogeneity, interoperability necessitates standardization.")
        self.assertGreater(easy, hard)


if __name__ == "__main__":
    unittest.main()
