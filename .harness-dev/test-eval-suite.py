#!/usr/bin/env python3
"""Black-box tests for the native runtime-v3 eval definitions."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check-eval-suite.py"


class EvalSuiteTests(unittest.TestCase):
    def test_repository_suite_and_scaffolds_pass(self):
        completed = subprocess.run(
            [sys.executable, str(CHECK)], text=True, capture_output=True, check=False
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("10 native plugin-eval cases", completed.stdout)

    def test_empty_suite_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, str(CHECK), "--eval-dir", directory],
                text=True, capture_output=True, check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("missing eval cases", completed.stdout)


if __name__ == "__main__":
    unittest.main()
