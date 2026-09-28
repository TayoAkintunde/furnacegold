"""Source verification, evidence chains and conflict resolution (Parts 5, 27, 28)."""
import unittest

from aibos.conflict import from_verification, resolve
from aibos.evidence import aggregate_verification, evidence_chain, quote_in_text
from aibos.registry import Registry
from aibos.rules import RULES
from aibos.schemas import ClaimKind, Verification
from tests.helpers import IsolatedTestCase, make_ctx

VERIFIERS = ["verification.source_quality", "verification.citation", "verification.primary_source",
             "verification.quote", "verification.statistics", "verification.date",
             "verification.cross_source", "verification.contradiction"]


class VerificationTests(IsolatedTestCase):
    def run_verifiers(self):
        ctx = make_ctx()
        reg = Registry.load()
        for aid in VERIFIERS:
            spec = reg.get(aid)
            o = RULES[spec.rule_name](ctx, spec)
            for k, v in o.data.items():
                ctx.merge(k, v, aid)
        aggregate_verification(ctx.claims, ctx.board["verification_reports"], ctx.sources)
        return ctx

    def test_supported_claim_becomes_fact(self):
        ctx = self.run_verifiers()
        c1 = next(c for c in ctx.claims if c.claim_id == "c1")
        self.assertEqual(c1.verification, Verification.SUPPORTED, c1.verification_notes)
        self.assertEqual(c1.kind, ClaimKind.FACT)
        self.assertGreater(c1.confidence, 0.8)

    def test_wrong_statistic_rejected(self):
        c2 = next(c for c in self.run_verifiers().claims if c.claim_id == "c2")
        # statistics check fails it, and the contradiction detector prefers c1 (supported by source text)
        self.assertIn(c2.verification, (Verification.UNSUPPORTED, Verification.CONTRADICTED))
        self.assertTrue(any("91" in n for n in c2.verification_notes))

    def test_fabricated_quote_rejected(self):
        c3 = next(c for c in self.run_verifiers().claims if c.claim_id == "c3")
        self.assertEqual(c3.verification, Verification.UNSUPPORTED)
        self.assertNotEqual(c3.kind, ClaimKind.FACT)   # assumption never silently becomes fact

    def test_uncited_claim_rejected(self):
        c4 = next(c for c in self.run_verifiers().claims if c.claim_id == "c4")
        self.assertEqual(c4.verification, Verification.UNSUPPORTED)
        self.assertEqual(c4.kind, ClaimKind.ASSUMPTION)

    def test_claims_from_agents_start_unverified(self):
        ctx = make_ctx()
        self.assertTrue(all(c.verification == Verification.UNVERIFIED for c in ctx.claims))

    def test_quote_matching_normalizes_typography(self):
        self.assertTrue(quote_in_text("it’s  available", "It's available today"))
        self.assertFalse(quote_in_text("", "anything"))

    def test_evidence_chain_fields(self):
        ctx = self.run_verifiers()
        link = evidence_chain(ctx.claims[0], ctx.sources)[0]
        for f in ("claim", "source", "evidence", "confidence", "interpretation", "decision"):
            self.assertTrue(str(getattr(link, f)), f)
        self.assertEqual(link.decision, "usable as fact")

    def test_conflicts_detected_and_resolved_toward_primary_evidence(self):
        ctx = self.run_verifiers()
        conflicts = from_verification(ctx)
        c2 = [c for c in conflicts if "c2" in c["description"]]
        self.assertTrue(c2)
        self.assertEqual(c2[0]["status"], "RESOLVED")
        self.assertIn("fail", c2[0]["resolution"])

    def test_disagreement_preserved_when_evidence_comparable(self):
        r = resolve("x", [{"agent": "a", "stance": "yes", "evidence_strength": 0.6},
                          {"agent": "b", "stance": "no", "evidence_strength": 0.55}], "verification.cross_source")
        self.assertEqual(r["status"], "PRESERVED")
        self.assertIn("verification.cross_source", r["resolution"])


if __name__ == "__main__":
    unittest.main()
