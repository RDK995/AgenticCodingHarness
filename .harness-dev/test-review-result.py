#!/usr/bin/env python3
"""Tests for durable terminal review-result validation."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check-review-result.py"


class ReviewResultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.result = {
            "schema_version": 1,
            "milestone_id": "P2-M7c",
            "cycle": 1,
            "base": "abc123",
            "head": "def456",
            "complete": True,
            "verdict": "PASS",
            "criteria": [
                {"id": "P2-M7c-AC1", "status": "PASS", "evidence": ["pytest: pass"]},
                {"id": "P2-M7c-AC2", "status": "PASS", "evidence": ["CLI: pass"]},
            ],
            "findings": [],
            "scope": "SUBSTANTIVE",
            "tier": "Mid",
            "model": "sonnet",
            "effort": "medium",
            "reason_code": "STANDARD_REVIEW",
        }
        self.state = {
            "milestones": {
                "P2-M7c": {
                    "criteria": [
                        {"id": "P2-M7c-AC1"},
                        {"id": "P2-M7c-AC2"},
                    ]
                }
            }
        }

    def run_check(self, result=None, *extra):
        result_path = self.root / "result.json"
        state_path = self.root / "state.json"
        result_path.write_text(json.dumps(result if result is not None else self.result))
        state_path.write_text(json.dumps(self.state))
        return subprocess.run(
            [sys.executable, str(CHECK), str(result_path), "--state", str(state_path),
             "--milestone", "P2-M7c", "--head", "def456", *extra],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_complete_pass_validates(self):
        completed = self.run_check()
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_incomplete_or_stale_result_fails_closed(self):
        for field, value, message in (
            ("complete", False, "not terminal"),
            ("head", "stale", "HEAD mismatch"),
        ):
            with self.subTest(field=field):
                result = dict(self.result, **{field: value})
                completed = self.run_check(result)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(message, completed.stderr)

    def test_missing_duplicate_and_unknown_criteria_fail(self):
        missing = dict(self.result, criteria=self.result["criteria"][:1])
        duplicate = dict(self.result, criteria=[self.result["criteria"][0]] * 2)
        unknown_item = {"id": "other", "status": "PASS", "evidence": ["x"]}
        unknown = dict(self.result, criteria=[*self.result["criteria"], unknown_item])
        for result, message in (
            (missing, "missing criteria"),
            (duplicate, "repeats criterion ids"),
            (unknown, "unknown criteria"),
        ):
            with self.subTest(message=message):
                completed = self.run_check(result)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(message, completed.stderr)

    def test_changes_required_needs_failed_criterion_or_blocking_finding(self):
        result = dict(
            self.result,
            verdict="CHANGES_REQUIRED",
            report_artifact=".harness/reviews/P2-M7c-cycle1.md",
        )
        completed = self.run_check(result)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requires a failed criterion", completed.stderr)
        result["criteria"] = [
            self.result["criteria"][0],
            {"id": "P2-M7c-AC2", "status": "FAIL", "evidence": ["missing"]},
        ]
        self.assertEqual(self.run_check(result).returncode, 0)

    def test_report_and_scope_contract_is_fail_closed(self):
        changes = dict(
            self.result,
            verdict="CHANGES_REQUIRED",
            criteria=[
                self.result["criteria"][0],
                {"id": "P2-M7c-AC2", "status": "FAIL", "evidence": ["missing"]},
            ],
        )
        completed = self.run_check(changes)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requires a .harness/reviews", completed.stderr)

        pass_with_report = dict(
            self.result,
            report_artifact=".harness/reviews/P2-M7c-cycle1.md",
        )
        completed = self.run_check(pass_with_report)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must be omitted", completed.stderr)

        pass_record_only = dict(self.result, scope="RECORD_ONLY")
        completed = self.run_check(pass_record_only)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("valid only for CHANGES_REQUIRED", completed.stderr)

    def test_truncated_json_is_never_terminal(self):
        result_path = self.root / "result.json"
        result_path.write_text('{"complete": true')
        completed = subprocess.run(
            [sys.executable, str(CHECK), str(result_path)],
            text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("cannot read valid review-result JSON", completed.stderr)


if __name__ == "__main__":
    unittest.main()
