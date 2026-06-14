from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from graphmind.models import MemoryCandidate
from graphmind.orchestrator import (
    apply_review_candidate,
    heuristic_intent,
    retrieve_agent,
    run_turn,
)
from graphmind.storage import LocalStore
from graphmind.scenarios import SCENARIOS


class GraphMindCoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = LocalStore(Path(self.tempdir.name) / "store.json")
        self.workspace_id = "test_ai_session"
        self.store.clone_scenario("AI Researcher", self.workspace_id, reset=True)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_clone_is_isolated(self):
        other_id = "test_ai_other"
        self.store.clone_scenario("AI Researcher", other_id, reset=True)
        self.assertNotEqual(self.workspace_id, other_id)
        self.assertEqual(len(self.store.list_memories(self.workspace_id)), len(self.store.list_memories(other_id)))

    def test_automatic_turn_writes_memory(self):
        before = len(self.store.list_memories(self.workspace_id))
        _, trace = run_turn(
            self.store,
            self.workspace_id,
            "I prefer compact visual dashboards",
            "AI Researcher",
            "Automatic",
        )
        after_memories = self.store.list_memories(self.workspace_id)
        after = len(after_memories)
        self.assertGreaterEqual(after, before + 1)
        self.assertGreaterEqual(len(trace.graph_delta.added_ids), 1)
        added = [memory for memory in after_memories if memory["id"] in trace.graph_delta.added_ids]
        self.assertTrue(any(memory["subject"] == "Dr. Lena Hoffmann" for memory in added))

    def test_observe_only_does_not_write(self):
        before = len(self.store.list_memories(self.workspace_id))
        _, trace = run_turn(
            self.store,
            self.workspace_id,
            "I prefer a completely command-line workflow",
            "AI Researcher",
            "Observe only",
        )
        after = len(self.store.list_memories(self.workspace_id))
        self.assertEqual(after, before)
        self.assertGreaterEqual(trace.graph_delta.ignored_count, 1)

    def test_review_candidate_can_be_applied(self):
        before = len(self.store.list_memories(self.workspace_id))
        candidate = MemoryCandidate(
            memory_type="skill",
            subject="Dr. Lena Hoffmann",
            relation="HAS_SKILL",
            object="Agent evaluation",
            confidence=0.9,
            importance=0.85,
            evidence="I have experience with agent evaluation.",
        )
        result = apply_review_candidate(self.store, self.workspace_id, candidate.model_dump())
        self.assertIn(result["persistence"], {"added", "updated"})
        self.assertGreaterEqual(len(self.store.list_memories(self.workspace_id)), before)

    def test_duplicate_confirms_existing_memory(self):
        candidate = MemoryCandidate(
            memory_type="preference",
            subject="Dr. Lena Hoffmann",
            relation="PREFERS",
            object="Modular system architectures",
            confidence=0.99,
            importance=0.95,
            evidence="I still prefer modular system architectures.",
        )
        result = apply_review_candidate(self.store, self.workspace_id, candidate.model_dump())
        self.assertEqual(result["persistence"], "updated")
        memory = next(m for m in self.store.list_memories(self.workspace_id) if m["id"] == result["memory_id"])
        self.assertEqual(memory["status"], "confirmed")
        self.assertGreaterEqual(memory["mention_count"], 2)

    def test_ai_research_projects_have_functional_components(self):
        memories = self.store.list_memories(self.workspace_id)
        projects = {"ReasonScope", "Orchestrix"}
        project_edges = [m for m in memories if m["relation"] == "CONTAINS" and m["subject"] in projects]
        self.assertEqual({m["subject"] for m in project_edges}, projects)
        self.assertGreaterEqual(len(project_edges), 10)
        self.assertTrue(any(m["subject"] == "Orchestrix" and m["relation"] == "PROVIDES_TRACES_TO" and m["object"] == "ReasonScope" for m in memories))
        self.assertTrue(any(m["subject"] == "Orchestrix" and m["relation"] == "USES_EVALUATION_FROM" and m["object"] == "ReasonScope" for m in memories))

    def test_ai_researcher_has_education_and_hobbies(self):
        memories = self.store.list_memories(self.workspace_id)
        self.assertTrue(any(m["relation"] == "COMPLETED_BACHELORS_AT" for m in memories))
        self.assertTrue(any(m["relation"] == "COMPLETED_MASTERS_AT" for m in memories))
        self.assertTrue(any(m["relation"] == "ENJOYS" and m["object"] == "Hiking" for m in memories))
        self.assertTrue(any(m["relation"] == "READS" and m["object"] == "Science-fiction novels" for m in memories))


    def test_ai_researcher_demo_prompts_are_balanced(self):
        prompts = SCENARIOS["AI Researcher"]["demo_prompts"]
        self.assertEqual(len(prompts), 3)
        self.assertIn("Orchestrix", prompts[0])
        self.assertIn("astronomy", prompts[1].lower())
        self.assertIn("Italian", prompts[2])

    def test_retrieval_modes(self):
        memories = self.store.list_memories(self.workspace_id)
        plan = heuristic_intent("How should Orchestrix use ReasonScope evaluation?", "AI Researcher")
        for mode in ["vector", "graph", "hybrid"]:
            rows = retrieve_agent("How should Orchestrix use ReasonScope evaluation?", memories, plan, mode_override=mode)
            self.assertTrue(rows)
            self.assertTrue(all(row["retrieval_mode"] == mode for row in rows))


if __name__ == "__main__":
    unittest.main()
