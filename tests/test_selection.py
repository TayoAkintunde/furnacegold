"""Agent selection (Part 41: agent selection)."""
import unittest

from aibos.registry import Registry
from aibos.selection import Selector, profile

DEMO = ("Find an important recent development in AI, research it, verify it, explain it to a beginner, "
        "turn it into several pieces of content, identify potential business opportunities, design one "
        "validation experiment, and produce a weekly-style opportunity report.")


class SelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = Registry.load()
        cls.sel = Selector(cls.reg)

    def llm_count(self, plan):
        return sum(1 for a in plan.agent_ids() if self.reg.get(a).executor == "llm")

    def test_profile_dimensions(self):
        p = profile(DEMO)
        self.assertEqual(p.complexity, "complex")
        self.assertIn("research", p.task_type)
        self.assertEqual(p.output_type, "report")
        for s in ("RESEARCH", "VERIFY", "KNOWLEDGE", "TEACH", "CONTENT", "OPPORTUNITY", "PRODUCT", "EXPERIMENT", "ANALYTICS_PLAN"):
            self.assertIn(s, p.stages)

    def test_simple_task_small_team(self):
        plan = self.sel.build_plan("Research the latest AI agent frameworks")
        self.assertEqual(plan.profile.complexity, "simple")
        self.assertTrue(1 <= self.llm_count(plan) <= 3, plan.agent_ids())
        self.assertIn("research.ai_agent", plan.agent_ids())

    def test_complex_task_bounded_team(self):
        plan = self.sel.build_plan(DEMO)
        n = self.llm_count(plan)
        self.assertTrue(8 <= n <= 20, n)
        self.assertLess(len(plan.agent_ids()), 60)
        self.assertLess(len(set(plan.agent_ids())), len(self.reg) / 5)   # never "activate everything"

    def test_high_risk_detected(self):
        self.assertEqual(profile("Publish the post and launch paid ads").risk_level.value, "HIGH")

    def test_named_platform_selected(self):
        plan = self.sel.build_plan("Write a TikTok script about MCP servers")
        self.assertIn("social.tiktok", plan.agent_ids())
        self.assertNotIn("social.linkedin", plan.agent_ids())

    def test_platform_formats_selected_precisely(self):
        social = lambda obj: sorted(a for a in self.sel.build_plan(obj).agent_ids() if a.startswith("social."))  # noqa: E731
        self.assertEqual(social("Research MCP servers and write a LinkedIn post"), ["social.linkedin"])
        self.assertEqual(social("Write an X thread about AI agents"), ["social.x_thread"])
        self.assertEqual(social("Make a LinkedIn carousel about RAG"), ["social.linkedin_carousel"])
        self.assertEqual(social("Create an Instagram carousel and a TikTok about robots"),
                         ["social.instagram_carousel", "social.tiktok"])

    def test_learner_level_selected(self):
        plan = self.sel.build_plan("Research vector databases and explain them to an advanced audience")
        self.assertIn("education.advanced_teacher", plan.agent_ids())
        self.assertNotIn("education.beginner_teacher", plan.agent_ids())

    def test_team_cap_enforced(self):
        plan = self.sel.build_plan(DEMO + " Also post on x, linkedin, instagram, tiktok, youtube, facebook, reddit, "
                                          "newsletter, blog, podcast.", complexity="simple")
        self.assertLessEqual(self.llm_count(plan), 3)
        self.assertTrue(any("team cap" in n for n in plan.notes))

    def test_pipelines_build(self):
        for name in ("content_factory", "education_factory", "product_factory", "revenue_factory", "daily_business", "weekly",
                     "teach_today", "record", "content_from_recording", "teaching_analytics"):
            plan = self.sel.build_plan(f"run {name}", pipeline=name)
            self.assertTrue(plan.steps, name)


if __name__ == "__main__":
    unittest.main()
