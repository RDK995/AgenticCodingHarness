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

    def write_re_entered_transcript(self, path, allowance=3, segments=4):
        """An agent woken by a completion notification after every `allowance` turns."""
        usage = {"input_tokens": 1, "cache_creation_input_tokens": 1,
                 "cache_read_input_tokens": 1, "output_tokens": 1}
        events, turn = [], 0
        for segment in range(segments):
            if segment:
                events.append({"type": "user", "message": {"content":
                    "[SYSTEM NOTIFICATION - NOT USER INPUT] <task-notification>"
                    "<status>completed</status></task-notification>"}})
            for _ in range(allowance):
                turn += 1
                events.append({"type": "assistant", "message": {
                    "id": f"turn-{turn}", "model": "claude-opus-5", "usage": usage,
                    "content": []}})
        path.write_text("\n".join(json.dumps(event) for event in events) + "\n")

    def test_segments_split_on_re_entry_so_an_evaded_cap_is_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent.jsonl"
            # 4 segments of 12 turns: 48 turns total against a 30-turn cap, with
            # no single segment anywhere near it.
            self.write_re_entered_transcript(path, allowance=12, segments=4)
            row = self.measure.analyse(path, "orchestrator", "M1", "", None,
                                       self.measure.DEFAULT_PRICES)
        self.assertEqual(row["api_turns"], 48)
        self.assertEqual(row["segments"], 4)
        self.assertEqual(row["re_entries"], 3)
        self.assertEqual(row["max_segment_turns"], 12)

        report = self.measure.aggregate([row], {"version": "test", "commit": None})
        evaded = report["summary"]["caps_evaded_by_re_entry"]
        self.assertEqual(report["summary"]["notification_re_entries"], 3)
        self.assertEqual(len(evaded), 1)
        self.assertEqual(evaded[0]["role"], "orchestrator")
        self.assertEqual(evaded[0]["max_segment_turns"], 12)
        # The blunt gate sees it too, but cannot say why; this is the why.
        self.assertTrue(report["summary"]["hard_limit_violations"])

    def test_anonymous_turns_are_counted_in_segments_too(self):
        """turns() falls back to anonymous-{index}; segment_turns must agree.

        An assistant event carrying usage but no message id is a real API turn.
        Dropped from the segment count, an over-limit transcript reports
        max_segment_turns 0, which satisfies `<= limit` and fabricates an evaded
        cap next to re_entries 0 — a false positive on the metric this change is
        judged by.
        """
        usage = {"input_tokens": 1, "cache_creation_input_tokens": 1,
                 "cache_read_input_tokens": 1, "output_tokens": 1}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent.jsonl"
            events = [{"type": "assistant", "message": {"model": "claude-opus-5",
                       "usage": usage, "content": []}} for _ in range(35)]
            path.write_text("\n".join(json.dumps(event) for event in events) + "\n")
            row = self.measure.analyse(path, "orchestrator", "M1", "", None,
                                       self.measure.DEFAULT_PRICES)
        self.assertEqual(row["api_turns"], 35)
        self.assertEqual(row["segments"], 1)
        self.assertEqual(row["max_segment_turns"], 35)
        self.assertEqual(row["re_entries"], 0)

        report = self.measure.aggregate([row], {"version": "test", "commit": None})
        self.assertTrue(report["summary"]["hard_limit_violations"])
        self.assertEqual(report["summary"]["caps_evaded_by_re_entry"], [])

    def test_one_long_segment_is_not_an_evaded_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent.jsonl"
            self.write_re_entered_transcript(path, allowance=40, segments=1)
            row = self.measure.analyse(path, "orchestrator", "M1", "", None,
                                       self.measure.DEFAULT_PRICES)
        self.assertEqual(row["segments"], 1)
        self.assertEqual(row["re_entries"], 0)
        report = self.measure.aggregate([row], {"version": "test", "commit": None})
        # Over its cap in one uninterrupted run: a real overrun, not an evasion.
        self.assertTrue(report["summary"]["hard_limit_violations"])
        self.assertEqual(report["summary"]["caps_evaded_by_re_entry"], [])

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
        for command in (
            "curl --max-time 5 http://localhost/health",
            "curl --max-time=5 http://localhost/health",
            "curl --max-time=.5 http://localhost/health",
            "curl -m0.5 http://localhost/health",
        ):
            with self.subTest(command=command):
                self.assertFalse(self.measure.is_polling(command))
        self.assertTrue(self.measure.is_polling("curl http://localhost/health"))
        self.assertTrue(self.measure.is_polling("curl --max-time=soon http://localhost/health"))


if __name__ == "__main__":
    unittest.main()
