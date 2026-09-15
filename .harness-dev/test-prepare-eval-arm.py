#!/usr/bin/env python3
"""Tests for zero-cost control/treatment eval materialization."""

import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "prepare-eval-arm.py"


def load_module():
    spec = importlib.util.spec_from_file_location("prepare_eval_arm", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PrepareEvalArmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "evals", self.root / "evals")

    def test_control_replaces_only_skill_name(self):
        destination = self.module.copy_arm(
            self.root, "control", ["01-namespaced-state"]
        )
        prompt = (destination / "01-namespaced-state" / "prompt.md").read_text()
        grader = (destination / "01-namespaced-state" / "graders" / "skill-fired.md").read_text()
        self.assertIn("/harness:implement`", prompt)
        self.assertNotIn("implement-v3", prompt + grader)

    def test_treatment_preserves_v3_and_refuses_overwrite(self):
        destination = self.module.copy_arm(
            self.root, "treatment", ["01-namespaced-state"]
        )
        self.assertIn(
            "implement-v3",
            (destination / "01-namespaced-state" / "prompt.md").read_text(),
        )
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.module.copy_arm(self.root, "treatment", ["01-namespaced-state"])


if __name__ == "__main__":
    unittest.main()
