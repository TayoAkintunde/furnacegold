"""Knowledge storage, experiment tracking, analytics, approvals (Part 41)."""
import os
import unittest
from pathlib import Path

from aibos import analytics
from aibos.approval import ApprovalQueue
from aibos.evidence import aggregate_verification
from aibos.experiments import ExperimentError, ExperimentStore, evaluate_ab, sample_size_per_variant, validate
from aibos.memory import Memory
from aibos.registry import Registry
from aibos.rules import RULES
from aibos.schemas import RunStatus
from tests.helpers import IsolatedTestCase, make_ctx


def run_rule(ctx, agent_id):
    spec = Registry.load().get(agent_id)
    o = RULES[spec.rule_name](ctx, spec)
    for k, v in o.data.items():
        ctx.merge(k, v, agent_id)
    return o


class KnowledgeTests(IsolatedTestCase):
    def test_only_verified_claims_become_knowledge(self):
        ctx = make_ctx(persist=True)
        for a in ("verification.citation", "verification.primary_source", "verification.statistics"):
            run_rule(ctx, a)
        aggregate_verification(ctx.claims, ctx.board["verification_reports"], ctx.sources)
        o = run_rule(ctx, "knowledge.research_to_knowledge")
        self.assertEqual([k["claim_ids"] for k in o.data["knowledge"]], [["c1"]])
        m = Memory()
        self.assertEqual(len(m.read("global", kind="verified_fact")), 1)
        self.assertEqual(len(m.read("project", kind="open_question")), 3)
        self.assertTrue(m.search("Widget-1 benchmark"))

    def test_memory_deduplicates(self):
        m = Memory()
        m.write("global", "note", {"a": 1})
        m.write("global", "note", {"a": 1})
        self.assertEqual(m.stats()["global"], 1)


class ExperimentTests(IsolatedTestCase):
    GOOD = {"name": "t", "experiment_type": "landing_page", "hypothesis": "If we add X, signups will increase by 2%",
            "method": "A/B", "metric": "signup_rate", "success_criteria": "p<0.05 and lift>0",
            "failure_criteria": "no lift"}

    def test_required_fields_enforced(self):
        self.assertIn("missing METRIC", validate({**self.GOOD, "metric": ""}))
        with self.assertRaises(ExperimentError):
            ExperimentStore().register({"name": "x"})

    def test_register_and_record_result(self):
        s = ExperimentStore()
        e = s.register(self.GOOD)
        self.assertEqual(e.result, "NOT RUN")
        r = s.record_result(e.experiment_id, "FAIL", "no lift", "stop")
        for f in ("hypothesis", "method", "metric", "result", "interpretation", "next_action"):
            self.assertTrue(r[f])

    def test_ab_statistics(self):
        r = evaluate_ab(100, 1000, 150, 1000)
        self.assertTrue(r["significant"])
        self.assertAlmostEqual(r["abs_lift"], 0.05)
        self.assertFalse(evaluate_ab(100, 1000, 104, 1000)["significant"])
        n = sample_size_per_variant(0.10, 0.02)
        self.assertTrue(3000 < n < 5000, n)

    def test_registrar_rejects_bad_experiment(self):
        ctx = make_ctx(False)
        ctx.board["experiments"] = [{"name": "vague", "hypothesis": "people like it"}]
        o = run_rule(ctx, "experiments.registrar")
        self.assertEqual(o.status, RunStatus.DEGRADED)
        self.assertIn("REJECTED", ctx.board["experiments"][0]["registration"])


class AnalyticsTests(IsolatedTestCase):
    def test_no_data_is_reported_not_invented(self):
        o = run_rule(make_ctx(False), "analytics.content")
        self.assertEqual(o.status, RunStatus.DEGRADED)
        self.assertIn("NO DATA", o.findings[0])

    def test_metrics_from_supplied_csv(self):
        d = Path(os.environ["AIBOS_DATA_DIR"]) / "metrics"
        d.mkdir(parents=True, exist_ok=True)
        rows = ["date,channel,asset_id,metric,value"]
        vals = [100, 110, 120, 130, 140, 150, 900]
        rows += [f"2026-09-0{i + 1},linkedin,p1,impressions,{v}" for i, v in enumerate(vals)]
        (d / "export.csv").write_text("\n".join(rows) + "\nbad,row\n")
        self.assertEqual(len(analytics.load_metrics()), 7)
        ctx = make_ctx(False)
        o = run_rule(ctx, "analytics.content")
        self.assertEqual(o.status, RunStatus.OK)
        t = run_rule(ctx, "analytics.trend")
        self.assertIn("up", t.findings[0])
        a = run_rule(ctx, "analytics.anomaly")
        self.assertIn("900", str(a.findings))


class ApprovalTests(IsolatedTestCase):
    def test_approval_does_not_fake_execution(self):
        q = ApprovalQueue()
        item = q.submit(category="publish_content", title="post", payload={"text": "hi"}, requested_by="a",
                        run_id="r", integration="linkedin_api")
        self.assertEqual(item["integration_status"], "NOT CONNECTED")
        done = q.decide(item["id"], approve=True)
        self.assertEqual(done["status"], "APPROVED")
        self.assertEqual(done["execution"], "NOT_EXECUTED")
        self.assertIn("NOT CONNECTED", done["execution_note"])

    def test_blocked_item_cannot_be_approved(self):
        q = ApprovalQueue()
        item = q.submit(category="publish_content", title="bad", payload={}, requested_by="a", run_id="r",
                        blocked_reasons=["hype: guaranteed"])
        with self.assertRaises(ValueError):
            q.decide(item["id"], approve=True)
        self.assertEqual(q.decide(item["id"], approve=False)["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
