#!/usr/bin/env python3
"""Tests for resumable, single-inspection external-job state."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "scripts" / "external-job.py"


class ExternalJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.harness = self.root / ".harness"
        (self.harness / "evidence").mkdir(parents=True)
        self.state = self.harness / "state.json"
        self.milestones = self.harness / "milestones.md"
        self.requirements = self.harness / "requirements.md"
        self.state.write_text(json.dumps({
            "schema_version": 2,
            "current_milestone": "M1",
            "approved_external_job_classes": ["paid-eval"],
            "requirements": {"FR1": "M1"},
            "milestones": {"M1": {
                "status": "IN_PROGRESS", "review_cycles": 0,
                "criteria": [{"id": "M1-AC1", "status": "PENDING", "text": "works", "evidence": []}],
                "tasks": [], "reviews": [], "findings": [], "validation": [],
                "follow_ups": [], "external_jobs": [],
                "as_built": {"artifact": None, "result": "PENDING"},
            }},
        }))
        self.milestones.write_text(
            "# Milestones\n\n## M1 — Work\n\nStatus: IN_PROGRESS\n\n"
            "### Acceptance Criteria\n\n- [ ] works\n"
        )
        self.requirements.write_text(
            "# Requirements\n\n## Functional Requirements\n\n- [FR1] works\n"
        )

    def run_command(self, action, *extra):
        return subprocess.run(
            [sys.executable, str(COMMAND), action, "--state", str(self.state),
             "--milestones", str(self.milestones), "--requirements", str(self.requirements),
             "--milestone", "M1", "--job-id", "eval-1", *map(str, extra)],
            text=True, capture_output=True, check=False,
        )

    def test_launch_wait_and_complete_without_duplicate_launch(self):
        launched = self.run_command(
            "launch", "--job-class", "paid-eval", "--owner", "controller",
            "--result-artifact", ".harness/evidence/eval-1.json",
        )
        self.assertEqual(launched.returncode, 0, launched.stderr)
        self.assertIn("WAITING_EXTERNAL", launched.stdout)
        duplicate = self.run_command(
            "launch", "--job-class", "paid-eval", "--owner", "controller",
            "--result-artifact", ".harness/evidence/eval-1.json",
        )
        self.assertNotEqual(duplicate.returncode, 0)
        waiting = self.run_command("inspect")
        self.assertEqual(waiting.returncode, 0, waiting.stderr)
        self.assertIn("WAITING_EXTERNAL", waiting.stdout)
        result = self.harness / "evidence" / "eval-1.json"
        result.write_text(json.dumps({"complete": True, "status": "COMPLETE", "summary": "passed"}))
        completed = self.run_command("inspect")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("COMPLETE", completed.stdout)
        job = json.loads(self.state.read_text())["milestones"]["M1"]["external_jobs"][0]
        self.assertEqual(job["status"], "COMPLETE")
        self.assertEqual(len(job["result_sha256"]), 64)

    def test_unapproved_class_and_escaping_path_fail(self):
        for job_class, artifact in (
            ("unknown", ".harness/evidence/eval-1.json"),
            ("paid-eval", "../outside.json"),
        ):
            completed = self.run_command(
                "launch", "--job-class", job_class, "--owner", "controller",
                "--result-artifact", artifact,
            )
            self.assertNotEqual(completed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
