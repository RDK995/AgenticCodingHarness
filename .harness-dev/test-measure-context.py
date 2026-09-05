#!/usr/bin/env python3
"""Black-box-ish tests for transcript efficiency reporting and release gates."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measure = load("measure_context", ROOT / ".harness-dev/measure-context.py")
        cls.release = load("check_efficiency", ROOT / ".harness-dev/check-efficiency.py")

    def write_transcript(self, path):
        usage = {"input_tokens": 10, "cache_creation_input_tokens": 20,
                 "cache_read_input_tokens": 30, "output_tokens": 40}
        events = [
            {"type": "assistant", "message": {"id": "one", "model": "claude-sonnet",
             "usage": usage, "content": [{"type": "tool_use", "name": "Bash",
             "input": {"command": "pytest -q"}}]}},
            {"type": "assistant", "message": {"id": "one", "model": "claude-sonnet",
             "usage": usage, "content": [{"type": "tool_use", "name": "Bash",
             "input": {"command": "pytest   -q"}}]}},
            {"type": "assistant", "message": {"id": "two", "model": "claude-sonnet",
             "usage": usage, "content": [{"type": "tool_use", "name": "Bash",
             "input": {"command": "sleep 5"}}]}},
        ]
        path.write_text("\n".join(json.dumps(event) for event in events) + "\n")

    def test_deduplicates_messages_and_reports_efficiency_signals(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent.jsonl"
            self.write_transcript(path)
            row = self.measure.analyse(path, "orchestrator", "M16 work", "", None,
                                       self.measure.DEFAULT_PRICES)
        self.assertEqual(row["api_turns"], 2)
        self.assertEqual(row["token_traffic"], 200)
        self.assertEqual(row["milestone"], "M16")
        self.assertEqual(row["polling_commands"], ["sleep 5"])
        self.assertEqual(row["duplicate_validation_commands"]["pytest -q"], 1)
        self.assertIsNotNone(row["estimated_cost_usd"])

    def test_aggregate_includes_role_milestone_parent_and_limits(self):
        row = {"role": "skill session", "milestone": "M1", "api_turns": 3,
               "token_traffic": 30, "estimated_cost_usd": 0.1, "peak_context": 20,
               "polling_commands": [], "duplicate_validation_commands": {},
               "record_only_review": False, "review_diff_ranges": [], "path": "parent"}
        worker = dict(row, role="worker", token_traffic=70, api_turns=46, path="worker")
        report = self.measure.aggregate([row, worker], {"version": "x", "commit": "y"})
        self.assertEqual(report["summary"]["parent_share"], 0.3)
        self.assertEqual(report["summary"]["workers_over_45_turns"], 1)
        self.assertEqual(len(report["summary"]["hard_limit_violations"]), 1)
        self.assertIn("worker", report["by_role"])
        self.assertIn("M1", report["by_milestone"])

    def test_release_gate_requires_accuracy_and_efficiency(self):
        report = {"summary": {"contexts": 5, "api_turns": 25, "token_traffic": 1000,
                  "polling_violations": 0, "hard_limit_violations": [],
                  "orchestrator_median_turns": 20, "workers_over_45_turns": 0,
                  "record_only_semantic_reviews": 0, "parent_share": 0.1},
                  "by_role": {role: {} for role in (
                      "skill session", "orchestrator", "worker", "verifier", "reviewer"
                  )}}
        accuracy = {"behavioural_fixtures_pass": True, "independent_verification": True,
                    "independent_milestone_review": True}
        self.assertTrue(all(self.release.check(report, accuracy).values()))
        report["summary"]["parent_share"] = 0.2
        self.assertFalse(self.release.check(report, accuracy)["parent traffic no more than 15%"])

    def test_empty_report_cannot_certify_a_release(self):
        report = self.measure.aggregate([], {"version": "x", "commit": "y"})
        accuracy = {"behavioural_fixtures_pass": True, "independent_verification": True,
                    "independent_milestone_review": True}
        gates = self.release.check(report, accuracy)
        self.assertFalse(gates["at least one context was measured"])
        self.assertFalse(gates["measured traffic and API turns are nonzero"])
        self.assertFalse(gates["all expected execution roles are present"])
        self.assertFalse(gates["a parent/controller context is present"])

    def test_partial_report_missing_reviewer_cannot_certify_a_release(self):
        roles = {"skill session": {}, "orchestrator": {}, "worker": {}, "verifier": {}}
        report = {"summary": {"contexts": 4, "api_turns": 20, "token_traffic": 1000,
                  "polling_violations": 0, "hard_limit_violations": [],
                  "orchestrator_median_turns": 20, "workers_over_45_turns": 0,
                  "record_only_semantic_reviews": 0, "parent_share": 0.1},
                  "by_role": roles}
        accuracy = {"behavioural_fixtures_pass": True, "independent_verification": True,
                    "independent_milestone_review": True}
        self.assertFalse(self.release.check(report, accuracy)["all expected execution roles are present"])

    def test_bounded_curl_is_not_polling(self):
        self.assertFalse(self.measure.is_polling("curl --max-time 5 http://localhost/health"))
        self.assertTrue(self.measure.is_polling("curl http://localhost/health"))


if __name__ == "__main__":
    unittest.main()
