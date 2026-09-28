"""End-to-end orchestration, opportunity generation, audit and CLI (Parts 24, 40, 41, 45)."""
import io
import json
import unittest
from contextlib import redirect_stdout

from aibos.approval import ApprovalQueue
from aibos.audit import run_audit
from aibos.backends import OfflineBackend, ScriptedBackend
from aibos.cli import main
from aibos.improvement import propose
from aibos.orchestrator import MasterOrchestrator
from aibos.paths import REGISTRY_DIR
from aibos.registry import Registry
from aibos.schemas import RunStatus
from tests.helpers import IsolatedTestCase, scripted_responses, sources

DEMO = ("Find an important recent development in AI, research it, verify it, explain it to a beginner, "
        "turn it into several pieces of content, identify potential business opportunities, design one "
        "validation experiment, and produce a weekly-style opportunity report.")


class EndToEndTests(IsolatedTestCase):
    def run_demo(self, backend):
        m = MasterOrchestrator(backend=backend)
        ctx = m.run(DEMO, sources(), complexity="complex")
        return ctx

    def test_scripted_full_chain(self):
        ctx = self.run_demo(ScriptedBackend(scripted_responses(), "unit-test script"))
        stages = [s["stage"] for s in ctx.stage_log]
        for s in ("RESEARCH", "VERIFY", "KNOWLEDGE", "TEACH", "CONTENT", "QUALITY", "OPPORTUNITY", "PRODUCT",
                  "EXPERIMENT", "ANALYTICS_PLAN", "APPROVAL", "SECURITY", "REPORT", "LEARN"):
            self.assertIn(s, stages)
        # verification: c1 verified, c2 (wrong statistic) excluded
        self.assertEqual([c.claim_id for c in ctx.verified_claims()], ["c1"])
        # injection source quarantined before research
        self.assertIn("s3", ctx.quarantined_sources)
        # content drafted, gated, and queued — never published
        self.assertTrue(ctx.board["content"])
        pending = ApprovalQueue().list("PENDING")
        self.assertTrue(pending)
        self.assertTrue(all(i["category"] == "publish_content" for i in pending))
        self.assertFalse(any(i["status"] in ("APPROVED",) for i in ApprovalQueue().list(None)))
        # opportunity + experiment recorded with required fields
        self.assertTrue(ctx.board["opportunities"])
        exp = ctx.board["experiments"][0]
        self.assertIn("PRE-REGISTERED", exp["registration"])
        self.assertIn("analytics_plan", ctx.board)
        report = (ctx.run_dir / "report.md").read_text()
        for section in ("1. RESEARCH", "2. VERIFY", "3. KNOWLEDGE", "4. TEACH", "5. CONTENT", "6. OPPORTUNITY",
                        "7. PRODUCT", "8. EXPERIMENT", "9. ANALYTICS PLAN", "Evidence chain"):
            self.assertIn(section, report)
        self.assertIn("Published externally:** nothing", report)
        self.assertIn("Weekly strategy report", report)          # objective asked for a weekly-style report
        self.assertIn("NO DATA", report)                          # no analytics supplied -> nothing invented
        run = json.loads((ctx.run_dir / "run.json").read_text())
        self.assertEqual(run["run_id"], ctx.run_id)

    def test_offline_run_is_honest(self):
        ctx = self.run_demo(OfflineBackend())
        research = next(o for o in ctx.outputs if o.agent_id.startswith("research."))
        self.assertEqual(research.status, RunStatus.NO_MODEL)
        self.assertEqual(ctx.claims, [])
        skipped = [s for s in ctx.stage_log if str(s.get("status", "")).startswith("SKIPPED")]
        self.assertTrue(any(s["stage"] == "CONTENT" for s in skipped))
        self.assertEqual(ApprovalQueue().list(None), [])
        self.assertTrue((ctx.run_dir / "prompts").exists())   # prompts saved for inspection

    def test_audit_and_proposals_never_modify_registry(self):
        before = {p.name: p.read_text() for p in REGISTRY_DIR.glob("*.yaml")}
        reg = Registry.load()
        a = run_audit(reg)
        self.assertTrue(a["duplicate_agents"])            # e.g. audience vs sales objection analysts
        self.assertEqual([m for m in a["missing_agents_or_capabilities"] if "reason" in m and "not implemented" in m["reason"]], [])
        props = propose(reg, a)
        self.assertTrue(all(p["status"] == "PENDING_HUMAN_REVIEW" and not p["auto_apply"] for p in props))
        after = {p.name: p.read_text() for p in REGISTRY_DIR.glob("*.yaml")}
        self.assertEqual(before, after)

    def test_cli_commands(self):
        for argv in (["/agents"], ["agents", "--family", "research"], ["plan", DEMO], ["integrations"],
                     ["audit", "--limit", "1"], ["pipeline"], ["knowledge"], ["approvals", "list"],
                     ["experiment", "list"], ["agent-status"], ["agent-test", "content_quality.hype"],
                     ["research", "AI", "agents", "--backend", "offline", "--no-persist"]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(argv)
            self.assertEqual(rc, 0, argv)
            self.assertTrue(buf.getvalue(), argv)


if __name__ == "__main__":
    unittest.main()
