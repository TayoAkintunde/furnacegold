"""Business profile: the template must contain no invented values; validation catches bad answers."""
import copy
import unittest

from aibos import profile

REQUIRED_SECTIONS = {
    "business", "expertise", "interests", "target_audience", "geographic_market", "content_platforms",
    "content_style", "business_goals", "revenue_goals", "current_products", "planned_products", "services",
    "technology_preferences", "strengths", "weaknesses", "available_time", "budget",
    "preferred_business_models", "topics_to_be_known_for", "topics_to_avoid", "other_notes",
}


class ProfileTemplateTests(unittest.TestCase):
    def setUp(self):
        self.p = profile.load()

    def test_template_has_every_section(self):
        self.assertTrue(REQUIRED_SECTIONS <= set(self.p), REQUIRED_SECTIONS - set(self.p))

    def test_template_contains_no_invented_values(self):
        rep = profile.check(self.p)
        self.assertEqual(rep.status, "NOT_ANSWERED")
        self.assertEqual([s for s, v in rep.sections.items() if v["filled"]], [])
        self.assertEqual(rep.errors, [])
        self.assertFalse(profile.is_configured(self.p))


class ProfileValidationTests(unittest.TestCase):
    def setUp(self):
        self.p = copy.deepcopy(profile.load())

    def test_partial_answers(self):
        self.p["interests"]["topics"] = ["something"]
        rep = profile.check(self.p)
        self.assertEqual(rep.status, "PARTIAL")
        self.assertNotIn("interests", rep.missing_sections)

    def test_rejects_unknown_platform_and_model(self):
        self.p["content_platforms"]["platforms"] = [{"platform": "myspace", "priority": 9}]
        self.p["preferred_business_models"]["ranked"] = ["pyramid_scheme"]
        errors = " | ".join(profile.check(self.p).errors)
        self.assertIn("myspace", errors)
        self.assertIn("priority", errors)
        self.assertIn("pyramid_scheme", errors)

    def test_rejects_contradictions_and_bad_numbers(self):
        self.p["topics_to_be_known_for"]["topics"] = ["AI agents"]
        self.p["topics_to_avoid"]["topics"] = [{"topic": "AI agents", "reason": "x"}]
        self.p["available_time"]["hours_per_week_total"] = 200
        self.p["budget"]["monthly_total"] = -5
        errors = " | ".join(profile.check(self.p).errors)
        for expected in ("known for", "hours_per_week_total", "monthly_total"):
            self.assertIn(expected, errors)

    def test_rejects_personal_data(self):
        self.p["other_notes"] = "contact me at someone@example.com"
        self.assertTrue(any("personal data" in e for e in profile.check(self.p).errors))

    def test_assumed_audience_is_flagged(self):
        self.p["target_audience"]["segments"] = [{"name": "x", "evidence": "assumption"}]
        self.assertTrue(any("hypothesis" in w for w in profile.check(self.p).warnings))


if __name__ == "__main__":
    unittest.main()
