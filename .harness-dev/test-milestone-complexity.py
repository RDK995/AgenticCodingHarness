#!/usr/bin/env python3
"""Static regression checks for operational milestone sizing."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MilestoneComplexityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.planning = (ROOT / "agents/references/planning.md").read_text()
        cls.fixture = (ROOT / "fixtures/13-operationally-oversized/EXPECTED.md").read_text()

    def test_operational_signals_are_explicit(self):
        for signal in (
            "SUBSYSTEMS_GT_3",
            "CONCURRENCY_LIFECYCLE",
            "IMPLEMENTATION_PLUS_LIVE_PROOF",
            "PRODUCTION_FILES_GT_8",
            "WORKER_TASKS_GT_6",
            "MULTIPLE_OUTCOMES",
        ):
            self.assertIn(signal, self.planning)

    def test_multiple_signals_force_a_pre_task_split(self):
        self.assertIn("Two or more require a split", self.planning)
        self.assertIn("before acceptance work\nor task packets are created", self.planning)

    def test_split_preserves_vertical_review_boundaries(self):
        self.assertIn("independently implementable", self.planning)
        self.assertIn("testable and reviewable", self.planning)
        self.assertIn("useful vertical slice", self.fixture)

    def test_criterion_count_is_not_the_only_measure(self):
        self.assertIn("They are not the sole measure", self.planning)
        self.assertIn("only four acceptance criteria", self.fixture)

    def test_small_coherent_changes_are_not_split_by_file_count_alone(self):
        self.assertIn("not split merely because it touches several files", self.planning)


if __name__ == "__main__":
    unittest.main()
