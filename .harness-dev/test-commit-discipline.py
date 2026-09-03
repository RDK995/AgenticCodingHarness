#!/usr/bin/env python3
"""Static regression tests for target-repository commit discipline."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CommitDisciplineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orchestrator = (ROOT / "agents" / "orchestrator.md").read_text()
        cls.fix_cycle = (ROOT / "agents" / "references" / "fix-cycle.md").read_text()
        cls.skill = (ROOT / "skills" / "implement" / "SKILL.md").read_text()
        cls.runtime = "\n".join((cls.orchestrator, cls.fix_cycle, cls.skill))

    def test_accepted_tasks_are_committed_by_explicit_path(self):
        self.assertIn("After each accepted task", self.orchestrator)
        self.assertIn("git add <the paths", self.orchestrator)
        self.assertIn("never `git add -A`", self.orchestrator)

    def test_correction_scope_is_a_commit_range(self):
        self.assertIn("Pre-correction: <sha>", self.fix_cycle)
        self.assertIn("git diff <Pre-correction> HEAD", self.fix_cycle)

    def test_snapshot_patch_mechanism_is_retired(self):
        self.assertNotIn("git commit-tree", self.runtime)
        self.assertNotIn("GIT_INDEX_FILE", self.runtime)
        self.assertNotIn("cycle<n>.patch", self.runtime)

    def test_history_mutation_and_remote_actions_are_forbidden(self):
        for phrase in ("Never push", "Never merge", "Never rewrite history", "Never `git stash`"):
            self.assertIn(phrase, self.orchestrator)
        self.assertNotIn("git reset --soft", self.runtime)

    def test_dirty_tree_requires_ownership_classification(self):
        self.assertIn("classify it before committing anything", self.orchestrator)
        self.assertIn("ownership or scope", self.orchestrator)
        self.assertIn("stop and ask the human", self.orchestrator)


if __name__ == "__main__":
    unittest.main()
