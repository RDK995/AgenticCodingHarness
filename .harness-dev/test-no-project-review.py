#!/usr/bin/env python3
"""Ensure all-DONE terminates without a project-level review."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = [
    ROOT / "README.md",
    ROOT / "agents" / "as-built.md",
    ROOT / "agents" / "orchestrator.md",
    ROOT / "agents" / "reviewer.md",
    ROOT / "agents" / "references" / "fix-cycle.md",
    ROOT / "skills" / "implement" / "SKILL.md",
    ROOT / "skills" / "implement" / "references" / "milestones-template.md",
    ROOT / "skills" / "scope-mvp" / "SKILL.md",
]


class NoProjectReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = "\n".join(path.read_text() for path in RUNTIME_FILES)
        cls.skill = (ROOT / "skills" / "implement" / "SKILL.md").read_text()

    def test_project_review_modes_are_absent(self):
        for forbidden in ("Final fresh review", "Final-review fix cycle", "final holistic review", "final review mode"):
            self.assertNotIn(forbidden, self.text)

    def test_compose_mode_and_drift_artifact_are_absent(self):
        self.assertNotIn("COMPOSE", self.text)
        self.assertNotIn(".harness/as-built/drift.md", self.text)

    def test_all_done_is_mechanical_and_terminal(self):
        self.assertIn("run the deterministic completion check", self.skill)
        self.assertIn("Do not invoke another reviewer", self.skill)
        self.assertIn("then STOP", self.skill)

    def test_affected_interface_integration_stays_in_milestone_review(self):
        reviewer = (ROOT / "agents" / "reviewer.md").read_text()
        self.assertIn("Existing consumers of an interface changed by this milestone", reviewer)


if __name__ == "__main__":
    unittest.main()
