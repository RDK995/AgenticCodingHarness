#!/usr/bin/env python3
"""Tests for fail-closed control/treatment economics comparison."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / ".harness-dev" / "compare-efficiency.py"


class CompareEfficiencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def report(self, arm, number, cost, tokens, retry=0, accurate=True):
        path = self.root / f"{arm}-{number}.json"
        path.write_text(json.dumps({
            "schema_version": 2,
            "manifest": {"arm": arm, "run_id": f"{arm}-{number}", "comparable": True},
            "summary": {
                "accepted_units": 1,
                "cost_per_accepted_unit_usd": cost,
                "tokens_per_accepted_unit": tokens,
                "retry_rate": retry,
            },
            "accuracy": {"passed": accurate},
        }))
        return path

    def run_check(self, controls, treatments):
        return subprocess.run(
            [sys.executable, str(CHECK), "--control", *map(str, controls),
             "--treatment", *map(str, treatments)],
            text=True, capture_output=True, check=False,
        )

    def test_passing_campaign(self):
        controls = [self.report("control", n, cost, tokens) for n, cost, tokens in (
            (1, 10, 1000), (2, 12, 1200), (3, 14, 1400)
        )]
        treatments = [self.report("treatment", n, cost, tokens) for n, cost, tokens in (
            (1, 8, 800), (2, 9, 900), (3, 10, 1000)
        )]
        completed = self.run_check(controls, treatments)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("PASS median accepted-task cost", completed.stdout)

    def test_cost_or_accuracy_regression_fails(self):
        controls = [self.report("control", n, 10, 1000) for n in range(3)]
        treatments = [self.report("treatment", n, 9, 900, accurate=n != 2) for n in range(3)]
        completed = self.run_check(controls, treatments)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("accuracy.passed must be true", completed.stdout)

    def test_too_few_or_wrong_arm_fails(self):
        controls = [self.report("control", n, 10, 1000) for n in range(2)]
        treatments = [self.report("treatment", n, 8, 800) for n in range(3)]
        completed = self.run_check(controls, treatments)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requires at least 3", completed.stdout)


if __name__ == "__main__":
    unittest.main()
