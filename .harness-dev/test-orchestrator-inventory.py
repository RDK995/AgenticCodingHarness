#!/usr/bin/env python3
"""Protect behavioural rules while keeping the orchestrator prompt compact."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OrchestratorInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / "agents/orchestrator.md").read_text()

    def test_core_stays_compact(self):
        # 700 until the dispatch-collect rule (2026-09-09) took 26 lines. The cap
        # exists to stop the core regrowing toward the 912 lines it was before the
        # phase split, not to freeze it; a rule every dispatch in both phases needs
        # belongs here rather than in a reference file both phases would load.
        self.assertLessEqual(len(self.text.splitlines()), 720)

    def test_behavioral_seams_remain(self):
        for phrase in (
            "You coordinate; you do not implement",
            "check its size and shape",
            "Creating task packets",
            "Delegate navigation",
            "Routing rule",
            "Task-level retry and escalation",
            "Verifying a task result",
            "Collect what you dispatch",
            "Git discipline in the target repository",
            "One fix cycle",
            "Milestone completion gate",
            "At 20, stop taking on new work and hand off",
            "check-state.py",
            "Human escalation contract",
        ):
            self.assertIn(phrase, self.text)

    def test_historical_measurement_narrative_is_not_runtime_prompt(self):
        for phrase in ("54% of every tool call", "Across 63 measured", "On a real milestone"):
            self.assertNotIn(phrase, self.text)


if __name__ == "__main__":
    unittest.main()
