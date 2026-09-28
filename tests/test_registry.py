"""Agent loading (Part 41: agent loading)."""
import unittest

import yaml

from aibos import config
from aibos.paths import PROMPTS_DIR, REGISTRY_DIR
from aibos.registry import Registry, RegistryError, expand_family
from aibos.rules import RULES
from aibos.schemas import REQUIRED_AGENT_FIELDS, AgentStatus, Level


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = Registry.load()

    def test_loads_hundreds_of_agents(self):
        self.assertGreaterEqual(len(self.reg), 300)

    def test_every_agent_has_required_fields(self):
        for a in self.reg.all():
            d = a.to_dict()
            for f in REQUIRED_AGENT_FIELDS:
                self.assertIn(f, d, a.agent_id)
            self.assertTrue(a.purpose.strip(), a.agent_id)
            self.assertNotIn("{", a.purpose, f"unformatted template in {a.agent_id}")

    def test_hierarchy_levels_present(self):
        levels = {a.level for a in self.reg.all()}
        self.assertTrue({Level.MASTER, Level.DOMAIN_ORCHESTRATOR, Level.SPECIALIST, Level.MICRO_SPECIALIST,
                         Level.QUALITY, Level.ANALYTICS_LEARNING} <= levels)
        self.assertEqual(len(self.reg.by_level(Level.MASTER)), 1)
        self.assertEqual(len(self.reg.by_level(Level.DOMAIN_ORCHESTRATOR)), 15)

    def test_statuses_valid(self):
        self.assertTrue(all(isinstance(a.status, AgentStatus) for a in self.reg.all()))

    def test_every_rule_executor_is_implemented(self):
        missing = [a.agent_id for a in self.reg.all() if a.is_rule and a.rule_name not in RULES]
        self.assertEqual(missing, [])

    def test_every_llm_agent_has_prompt_template(self):
        missing = [a.agent_id for a in self.reg.all()
                   if a.executor == "llm" and not (PROMPTS_DIR / f"{a.prompt_template}.md").exists()]
        self.assertEqual(missing, [])

    def test_platform_params_resolve(self):
        plats = config.platforms()
        for a in self.reg.by_family("social"):
            self.assertIn(a.params["platform"], plats, a.agent_id)

    def test_stage_and_pipeline_references_exist(self):
        for name, st in config.stages()["stages"].items():
            ag = st.get("agents", [])
            for lst in (ag.values() if isinstance(ag, dict) else [ag]):
                for a in lst:
                    self.assertIn(a, self.reg, f"stage {name} -> {a}")
        for name, p in config.pipelines().items():
            for step in p["steps"]:
                for a in step.get("agents", []) or []:
                    self.assertIn(a, self.reg, f"pipeline {name} -> {a}")

    def test_template_expansion_and_overrides(self):
        doc = yaml.safe_load((REGISTRY_DIR / "research.yaml").read_text())
        specs = expand_family(doc)
        papers = next(s for s in specs if s.agent_id == "research.papers")
        self.assertIn("arxiv", papers.tools)          # extra_tools appended
        self.assertIn("web_search", papers.tools)     # defaults kept
        self.assertIn("technical papers", papers.purpose)

    def test_unknown_dependency_rejected(self):
        a = self.reg.get("research.ai_news")
        import dataclasses
        bad = dataclasses.replace(a, agent_id="x.bad", dependencies=["does.not.exist"])
        with self.assertRaises(RegistryError):
            Registry([bad])

    def test_duplicate_ids_rejected(self):
        a = self.reg.get("research.ai_news")
        with self.assertRaises(RegistryError):
            Registry([a, a])


if __name__ == "__main__":
    unittest.main()
