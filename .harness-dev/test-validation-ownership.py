#!/usr/bin/env python3
"""Static tests for single-owner validation and compact evidence."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ValidationOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker = (ROOT / "agents" / "worker.md").read_text()
        cls.verifier = (ROOT / "agents" / "verifier.md").read_text()
        cls.reviewer = (ROOT / "agents" / "reviewer.md").read_text()
        cls.orchestrator = (ROOT / "agents" / "orchestrator.md").read_text()

    def test_worker_and_verifier_write_separate_evidence(self):
        self.assertIn("<task-id>-worker.log", self.worker)
        self.assertIn("<task-id>-verifier.log", self.verifier)

    def test_returns_are_summaries_not_full_logs(self):
        self.assertIn("return only the command, exit", self.worker)
        self.assertIn("Quote only the result or", self.verifier)

    def test_reviewer_owns_milestone_validation_once(self):
        self.assertIn("Run the milestone acceptance command", self.reviewer)
        self.assertIn("<milestone>-review.log", self.reviewer)

    def test_orchestrator_does_not_normally_run_tests(self):
        self.assertIn("Do not run task or", self.orchestrator)
        self.assertIn("unless two evidence artifacts contradict", self.orchestrator)


if __name__ == "__main__":
    unittest.main()
