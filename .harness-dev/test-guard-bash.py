#!/usr/bin/env python3
"""Black-box tests for the plugin's Bash safety hook."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "guard-bash.py"


class GuardBashTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def run_hook(self, command, *, session="session-1", agent="worker-1"):
        payload = {
            "hook_event_name": "PreToolUse",
            "session_id": session,
            "agent_id": agent,
            "agent_type": "harness:worker",
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }
        env = os.environ.copy()
        env["HARNESS_GUARD_STATE_DIR"] = self.temp.name
        completed = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(completed.stderr, "")
        self.assertEqual(completed.returncode, 0)
        return json.loads(completed.stdout)

    @staticmethod
    def decision(result):
        return result["hookSpecificOutput"]["permissionDecision"]

    def test_denies_foreground_sleep(self):
        result = self.run_hook("run-check; sleep 30; run-check")
        self.assertEqual(self.decision(result), "deny")
        self.assertIn("foreground sleep", result["hookSpecificOutput"]["permissionDecisionReason"])

    def test_denies_shell_poll_loop(self):
        for command in (
            "until test -f ready; do true; done",
            "while ! curl --max-time 2 http://localhost/ready; do true; done",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(self.run_hook(command)), "deny")

    def test_denies_unbounded_network_check(self):
        result = self.run_hook("curl http://localhost/ready")
        self.assertEqual(self.decision(result), "deny")
        self.assertIn("explicit timeout", result["hookSpecificOutput"]["permissionDecisionReason"])

    def test_allows_one_bounded_readiness_check(self):
        result = self.run_hook("curl --max-time 5 http://localhost/ready")
        self.assertEqual(self.decision(result), "allow")

    def test_denies_repeated_identical_readiness_check(self):
        command = "curl --max-time 5 http://localhost/ready"
        self.assertEqual(self.decision(self.run_hook(command)), "allow")
        result = self.run_hook(command)
        self.assertEqual(self.decision(result), "deny")
        self.assertIn("already ran", result["hookSpecificOutput"]["permissionDecisionReason"])

    def test_repeat_tracking_is_scoped_to_agent(self):
        command = "curl --max-time 5 http://localhost/ready"
        self.assertEqual(self.decision(self.run_hook(command, agent="worker-1")), "allow")
        self.assertEqual(self.decision(self.run_hook(command, agent="worker-2")), "allow")

    def test_allows_repeated_non_wait_validation(self):
        for _ in range(3):
            result = self.run_hook("python -m unittest discover -q")
            self.assertEqual(self.decision(result), "allow")

    def test_malformed_input_fails_closed(self):
        env = os.environ.copy()
        env["HARNESS_GUARD_STATE_DIR"] = self.temp.name
        completed = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not-json",
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        result = json.loads(completed.stdout)
        self.assertEqual(self.decision(result), "deny")


if __name__ == "__main__":
    unittest.main()
