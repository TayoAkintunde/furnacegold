"""Screen-recorded teaching: gates, scoring, recording checks, transcript, workflow, learning loop, end to end."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from aibos.approval import ApprovalQueue
from aibos.cli import main
from aibos.evidence import aggregate_verification
from aibos.registry import Registry
from aibos.rules import RULES
from aibos.rules.teaching import parse_transcript
from aibos.teaching_db import TeachingDB, WorkflowError
from tests import teaching_fixtures as F
from tests.helpers import FIXTURES, IsolatedTestCase, make_ctx

REG = Registry.load()


def run(ctx, agent_id):
    spec = REG.get(agent_id)
    o = RULES[spec.rule_name](ctx, spec)
    for k, v in o.data.items():
        ctx.merge(k, v, agent_id)
    return o


def verified_ctx():
    ctx = make_ctx()
    for a in ("verification.citation", "verification.primary_source", "verification.statistics", "verification.contradiction"):
        run(ctx, a)
    aggregate_verification(ctx.claims, ctx.board["verification_reports"], ctx.sources)
    return ctx


def cli(*argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(list(argv))
    return rc, buf.getvalue()


class GateAndScoreTests(IsolatedTestCase):
    def scored(self, opps):
        ctx = verified_ctx()
        ctx.board["teaching_opportunities"] = [dict(o) for o in opps]
        run(ctx, "teaching.value_gate")
        run(ctx, "teaching.scorer")
        return ctx, {r["opp_id"]: r for r in ctx.board["teaching_scores"]}

    def test_selects_demonstrable_well_evidenced_topic(self):
        ctx, rows = self.scored([F.GOOD, F.NOT_DEMO, F.WEAK])
        self.assertEqual([s["opp_id"] for s in ctx.board["teaching_selection"]], ["t1"])
        self.assertFalse(rows["t1"]["rejected"], rows["t1"])
        self.assertTrue(any("demonstrated" in r for r in rows["t2"]["reasons"]))
        self.assertTrue(any("value-first" in r for r in rows["t3"]["reasons"]))
        self.assertTrue(any("verified" in r or "evidence" in r for r in rows["t3"]["reasons"]))

    def test_unjustified_judgement_scores_zero(self):
        bad = dict(F.GOOD, judgements={k: {"score": 5, "justification": ""} for k in F.JUDGED})
        _, rows = self.scored([bad])
        self.assertEqual(rows["t1"]["breakdown"]["practical_usefulness"], 0.0)
        self.assertTrue(rows["t1"]["rejected"])      # no longer demonstrable -> gated

    def test_newness_from_verified_dates_only(self):
        _, rows = self.scored([F.GOOD])
        self.assertIn("newest verified date", " ".join(rows["t1"]["notes"]))

    def test_audience_interest_is_neutral_without_data(self):
        _, rows = self.scored([F.GOOD])
        self.assertEqual(rows["t1"]["breakdown"]["audience_interest"], 0.5)
        self.assertIn("NO DATA", " ".join(rows["t1"]["notes"]))

    def test_nothing_selected_when_all_fail(self):
        ctx, _ = self.scored([F.NOT_DEMO, F.WEAK])
        self.assertEqual(ctx.board["teaching_selection"], [])
        self.assertTrue(any("recording nothing" in e for e in ctx.escalations))


class RecordingCheckTests(IsolatedTestCase):
    def gate(self, plans=None, scripts=None, agent="teaching.feasibility"):
        ctx = verified_ctx()
        ctx.board["recording_plans"] = plans or []
        ctx.board["scripts"] = scripts or []
        run(ctx, agent)
        return {r["artifact_id"]: r for r in ctx.board["quality_reports"]}

    def test_good_plan_passes_feasibility(self):
        r = self.gate([F.PLAN])["plan-t1"]
        self.assertFalse([i for i in r["issues"] if i["severity"] == "BLOCKING"], r)

    def test_incomplete_plan_blocked(self):
        r = self.gate([dict(F.PLAN, proof="", demonstration=F.PLAN["demonstration"][:2])])["plan-t1"]
        msgs = " ".join(i["message"] for i in r["issues"] if i["severity"] == "BLOCKING")
        self.assertIn("proof", msgs)
        self.assertIn("demonstration steps", msgs)

    def test_script_quality(self):
        good = self.gate(scripts=[F.SCRIPT], agent="teaching.script_quality")["teaching.script_writer-1"]
        self.assertFalse([i for i in good["issues"] if i["severity"] in ("BLOCKING", "WARN")], good)
        hype = dict(F.SCRIPT, sections=[s for s in F.SCRIPT["sections"] if s["section"] not in ("caveat", "mistake")],
                    text=F.SCRIPT["text"] + " Act now, this revolutionary tool will supercharge everything!")
        bad = self.gate(scripts=[hype], agent="teaching.script_quality")["teaching.script_writer-1"]
        msgs = " ".join(i["message"] for i in bad["issues"])
        for expected in ("fake urgency", "caveat", "mistake", "marketing"):
            self.assertIn(expected, msgs)

    def test_technical_identifiers(self):
        s = dict(F.SCRIPT, text=F.SCRIPT["text"] + " Call `widget-1` then run `made-up-model-7` and grep_search().")
        r = self.gate(scripts=[s], agent="teaching.technical_check")["teaching.script_writer-1"]
        warn = " ".join(i["message"] for i in r["issues"] if i["severity"] == "WARN")
        self.assertIn("made-up-model-7", warn)
        self.assertNotIn("'widget-1'", warn)

    def test_structural_numbers_not_hallucinations(self):
        ctx = verified_ctx()
        ctx.board["scripts"] = [dict(F.SCRIPT, text="In step 3, wait 10 seconds. At 02:15 it scores 87.5% on the test.\nChapters\n00:00 Intro\n01:10 Setup")]
        run(ctx, "content_quality.hallucination")
        self.assertFalse(ctx.board["quality_reports"][0]["issues"])

    def test_value_first_blocks_generic(self):
        ctx = verified_ctx()
        ctx.board["content"] = [{"artifact_id": "a", "platform": "x_post", "text": "hi", "value_statement": "learn about AI"}]
        run(ctx, "content_quality.value_first")
        self.assertEqual(ctx.board["quality_reports"][0]["issues"][0]["severity"], "BLOCKING")


class TranscriptTests(unittest.TestCase):
    def test_parse_srt(self):
        t = parse_transcript(F.TRANSCRIPT)
        self.assertEqual(t["format"], "srt/vtt")
        self.assertEqual(len(t["segments"]), 3)
        self.assertEqual(t["duration_s"], 90.0)
        self.assertIn("87.5%", t["text"])

    def test_parse_plain_with_timestamps(self):
        t = parse_transcript("[00:00] hello there\n[01:05] now we run it\nno timestamp line")
        self.assertEqual(t["format"], "plain")
        self.assertEqual(t["duration_s"], 65)


class WorkflowTests(IsolatedTestCase):
    def test_transitions_enforced(self):
        db = TeachingDB()
        i = db.upsert({"topic": "x", "date_discovered": "2026-09-28"})
        self.assertEqual(i["status"], "RESEARCHED")
        with self.assertRaises(WorkflowError):
            db.transition(i["id"], "SELECTED", "system")          # human decision
        with self.assertRaises(WorkflowError):
            db.transition(i["id"], "RECORDED", "owner")           # skips a state
        db.transition(i["id"], "SELECTED", "owner")
        with self.assertRaises(WorkflowError):
            db.transition(i["id"], "READY_TO_RECORD", "owner")    # system sets this after /record
        db.transition(i["id"], "READY_TO_RECORD", "system")
        for s in ("RECORDED", "EDITING", "READY_TO_PUBLISH"):
            db.transition(i["id"], s, "owner")
        with self.assertRaises(WorkflowError):
            db.transition(i["id"], "PUBLISHED", "owner")          # needs the URL where the owner published it
        with self.assertRaises(WorkflowError):
            db.transition(i["id"], "PUBLISHED", "system", published_urls=["u"])   # system never publishes
        self.assertEqual(db.transition(i["id"], "PUBLISHED", "owner", published_urls=["https://example.com/v"])["status"],
                         "PUBLISHED")


class EndToEndTeachingTests(IsolatedTestCase):
    def responses(self, d):
        p = Path(self._tmp) / f"resp_{len(os.listdir(self._tmp))}.json"
        p.write_text(json.dumps({"provenance": "unit-test script", "responses": d}))
        return str(p)

    def test_full_teaching_workflow(self):
        src = str(FIXTURES / "sources.json")
        rc, out = cli("/teach-today", "--sources", src, "--responses", self.responses(F.teach_today_responses()))
        self.assertEqual(rc, 0, out)
        self.assertIn("TODAY'S SCREEN RECORDING: Evaluate Widget-1", out)
        db = TeachingDB()
        rec = [i for i in db.all() if i.get("recommended")]
        self.assertEqual(len(rec), 1)
        item = rec[0]
        self.assertEqual(item["status"], "RESEARCHED")
        for f in ("topic", "sources", "source_quality", "what_changed", "audience", "problem_solved", "teaching_angle",
                  "demo_idea", "recording_plan", "script", "difficulty", "estimated_recording_time", "content_formats",
                  "service_opportunity", "claims"):
            self.assertTrue(item.get(f), f)
        self.assertEqual({i["status"] for i in db.all() if not i.get("recommended")}, {"REJECTED"})
        brief = next(Path(self._tmp).glob("runs/*/teach_today.md")).read_text()
        for s in ("TODAY'S AI RADAR", "TODAY'S TEACHING OPPORTUNITIES", "TODAY'S SCREEN RECORDING", "Spoken script",
                  "Repurposing plan", "TODAY'S BUSINESS OPPORTUNITY", "consulting"):
            self.assertIn(s, brief)
        self.assertEqual(ApprovalQueue().list(None), [])          # nothing to publish yet

        # /record refuses until the owner selects the topic
        rc, out = cli("/record", item["id"], "--responses", self.responses(F.record_responses()))
        self.assertEqual(rc, 1)
        self.assertIn("teaching select", out)
        cli("teaching", "select", item["id"], "--by", "owner")
        rc, out = cli("/record", item["id"], "--responses", self.responses(F.record_responses()))
        self.assertEqual(rc, 0, out)
        self.assertEqual(db.get(item["id"])["status"], "READY_TO_RECORD")
        pkg = (Path(self._tmp) / "teaching" / item["id"] / "recording_package.md").read_text()
        for s in ("Before you press record", "Recording plan", "Spoken script", "Multi-level versions", "Production"):
            self.assertIn(s, pkg)

        # /content-from-recording from the owner's transcript
        tr = Path(self._tmp) / "rec.srt"
        tr.write_text(F.TRANSCRIPT)
        rc, out = cli("/content-from-recording", item["id"], "--transcript", str(tr),
                      "--responses", self.responses(F.content_responses()))
        self.assertEqual(rc, 0, out)
        self.assertEqual(db.get(item["id"])["status"], "RECORDED")
        pending = ApprovalQueue().list("PENDING")
        self.assertEqual(len(pending), 3)
        self.assertTrue(all(p["category"] == "publish_content" for p in pending))
        cp = (Path(self._tmp) / "teaching" / item["id"] / "content_package.md").read_text()
        self.assertIn("Formats missing", cp)                         # only 3 of 14 formats supplied -> reported

        # owner publishes; system analyses only supplied data
        for s in ("EDITING", "READY_TO_PUBLISH"):
            cli("teaching", "advance", item["id"], s, "--by", "owner")
        rc, _ = cli("teaching", "advance", item["id"], "PUBLISHED", "--by", "owner", "--url", "https://example.com/v")
        self.assertEqual(rc, 0)
        (Path(self._tmp) / "metrics").mkdir(exist_ok=True)
        rows = ["date,channel,asset_id,metric,value"] + [f"2026-09-30,youtube,{item['id']},{m},{v}" for m, v in
                (("views", 1200), ("retention_at_0s", 1.0), ("retention_at_15s", 0.8), ("retention_at_60s", 0.35),
                 ("retention_at_120s", 0.3))]
        (Path(self._tmp) / "metrics" / "yt.csv").write_text("\n".join(rows) + "\n")
        (Path(self._tmp) / "feedback").mkdir(exist_ok=True)
        (Path(self._tmp) / "feedback" / f"{item['id']}_comments.txt").write_text(
            "How do I score the answers automatically?\nHow can I score answers automatically?\nGreat video\n")
        rc, out = cli("teaching", "analyze", item["id"])
        self.assertEqual(rc, 0, out)
        done = db.get(item["id"])
        self.assertEqual(done["status"], "ANALYZED")
        self.assertEqual(done["performance"]["biggest_dropoff"]["from_s"], 15)
        self.assertTrue(done["performance"]["repeated_questions"])
        self.assertTrue(db.learning()["requested_topics"])       # feeds tomorrow's topic selection

    def test_offline_teach_today_is_honest(self):
        rc, out = cli("teach-today", "--sources", str(FIXTURES / "sources.json"), "--backend", "offline")
        self.assertEqual(rc, 0)
        self.assertIn("none", out)
        self.assertEqual(TeachingDB().all(), [])


if __name__ == "__main__":
    unittest.main()
