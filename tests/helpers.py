"""Shared test helpers: isolated data dir + fixture loaders + scripted responses."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FIXED_TODAY = "2026-09-10"


class IsolatedTestCase(unittest.TestCase):
    """Every test gets its own AIBOS_DATA_DIR so runs never touch real data."""

    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="aibos_test_")
        self._old = os.environ.get("AIBOS_DATA_DIR")
        os.environ["AIBOS_DATA_DIR"] = self._tmp

    def tearDown(self) -> None:
        if self._old is None:
            os.environ.pop("AIBOS_DATA_DIR", None)
        else:
            os.environ["AIBOS_DATA_DIR"] = self._old
        shutil.rmtree(self._tmp, ignore_errors=True)


def sources():
    from aibos.evidence import SourceStore
    return SourceStore.from_file(FIXTURES / "sources.json")


def claims_raw():
    return json.loads((FIXTURES / "claims.json").read_text())


def content_raw():
    return json.loads((FIXTURES / "content.json").read_text())


def make_ctx(with_claims=True, with_content=False, persist=False):
    from aibos.context import RunContext
    from aibos.registry import Registry
    ctx = RunContext("test objective", sources(), persist=persist, registry=Registry.load(), today=FIXED_TODAY)
    if with_claims:
        ctx.add_claims(claims_raw(), "fixture")
    if with_content:
        ctx.board["content"] = content_raw()
    return ctx


def structured(data: dict, findings=None, confidence=0.8) -> dict:
    return {"TASK": "t", "FINDINGS": findings or ["ok"], "EVIDENCE": [], "ASSUMPTIONS": [],
            "UNCERTAINTIES": [], "RECOMMENDATIONS": [], "NEXT_ACTION": "next", "CONFIDENCE": confidence,
            "SOURCES": ["s1"], "DATA": data}


def scripted_responses() -> dict:
    content = content_raw()[0]
    return {
        "research.ai_news": structured({"claims": claims_raw()[:1] + [claims_raw()[1]],
                                        "findings": [{"development": "Widget-1 release", "why_it_matters": "cheaper agents",
                                                      "claim_ids": ["c1"]}]}),
        "research.ai_model": structured({"claims": [], "findings": []}),
        "research.ai_agent": structured({"claims": [], "findings": []}),
        "education.beginner_teacher": structured({"explanations": [{
            "artifact_id": "expl-1", "level": "beginner", "title": "Widget-1 in plain terms",
            "text": content["text"], "glossary": {"benchmark": "a standard test"},
            "takeaways": ["re-run your own tests"], "claim_ids": ["c1"], "source_ids": ["s1"]}]}),
        "content_strategy.strategist": structured({"content_angles": [{"angle_id": "a1", "title": "What the benchmark means",
                                                                       "audience": "builders", "audience_evidence": "HYPOTHESIS",
                                                                       "key_claim_ids": ["c1"]}]}),
        "social.linkedin": structured({"content": [dict(content, artifact_id="social.linkedin-1")]}),
        "social.x_thread": structured({"content": [{"artifact_id": "social.x_thread-1", "platform": "x_thread",
                                                    "title": "thread", "claim_ids": ["c1"],
                                                    "text": "1/ ExampleAI released Widget-1: 87.5% on the Example benchmark (source: ExampleAI).\n---\n2/ A benchmark is a standard test. For example, the same questions for every model.\n---\n3/ Takeaway: re-run your own evaluations before switching."}]}),
        "social.newsletter": structured({"content": []}),
        "product_discovery.opportunity": structured({"opportunities": [{"id": "o1", "title": "Evaluation service",
                                                                         "problem": "teams cannot compare models",
                                                                         "evidence_claim_ids": ["c1"],
                                                                         "assumptions": ["teams will pay"], "risks": ["crowded"],
                                                                         "confidence": 0.4}]}),
        "revenue.model_researcher": structured({"revenue_models": [{"title": "fixed-fee audit", "assumptions": ["demand"]}]}),
        "product_discovery.mvp": structured({"products": [{"title": "Model-switch checklist", "cheapest_test": "landing page"}]}),
        "experiments.design": structured({"experiments": [{
            "name": "Checklist demand test", "experiment_type": "validation",
            "hypothesis": "If we offer the checklist, at least 5% of visitors will sign up",
            "method": "landing page with signup", "metric": "signup_rate",
            "success_criteria": ">= 5% of >= 300 visitors", "failure_criteria": "< 2% of >= 300 visitors",
            "data": {"baseline_rate": 0.03, "mde_abs": 0.02}}]}),
    }
