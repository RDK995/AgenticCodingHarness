#!/usr/bin/env python3
"""Tests for fail-closed v3 runtime preflight checks."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts" / "runtime-preflight.py"


class RuntimePreflightTests(unittest.TestCase):
    def run_preflight(self, version, *extra):
        return subprocess.run(
            [sys.executable, str(PREFLIGHT), "--plugin-root", str(ROOT),
             "--claude-version", version, *map(str, extra)],
            text=True, capture_output=True, check=False,
        )

    def test_old_runtime_fails_with_minimum_version(self):
        completed = self.run_preflight("2.1.236 (Claude Code)")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Required: Claude Code >= 2.1.269", completed.stderr)

    def test_supported_runtime_passes_static_contract(self):
        completed = self.run_preflight("2.1.269 (Claude Code)")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_live_evidence_requires_parent_child_and_foreground_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            audit_path = Path(directory) / "audit.jsonl"
            evidence = {
                "complete": True,
                "plugin_root": str(ROOT),
                "hook_probes": {
                    "parent": {"safe_allowed": True, "bounded_curl_allowed": True,
                               "sleep_denied": True},
                    "child": {"safe_allowed": True, "bounded_curl_allowed": True,
                              "sleep_denied": True},
                },
                "foreground": {"dispatched": 2, "returned": 2,
                               "initiating_turn": True,
                               "notification_re_entries": 0,
                               "polling_violations": 0},
            }
            evidence_path.write_text(json.dumps(evidence))
            events = [
                {"agent_type": "top-level", "decision": "deny",
                 "rule_id": "FOREGROUND_SLEEP"},
                {"agent_type": "harness:worker", "decision": "deny",
                 "rule_id": "FOREGROUND_SLEEP"},
            ]
            audit_path.write_text("\n".join(json.dumps(item) for item in events) + "\n")
            completed = self.run_preflight(
                "2.1.269", "--live-evidence", evidence_path, "--audit-log", audit_path
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            evidence["foreground"]["notification_re_entries"] = 1
            evidence_path.write_text(json.dumps(evidence))
            failed = self.run_preflight(
                "2.1.269", "--live-evidence", evidence_path, "--audit-log", audit_path
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("FAIL zero notification re-entry", failed.stdout)


if __name__ == "__main__":
    unittest.main()
