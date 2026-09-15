#!/usr/bin/env python3
"""Black-box tests for guarded schema-v2 state transitions."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRANSITION = ROOT / "scripts" / "transition-state.py"
CHECK = ROOT / "scripts" / "check-state.py"


class TransitionStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.harness = self.root / ".harness"
        self.harness.mkdir()
        (self.harness / "reviews").mkdir()
        self.state_path = self.harness / "state.json"
        self.milestones_path = self.harness / "milestones.md"
        self.requirements_path = self.harness / "requirements.md"
        self.state = {
            "schema_version": 2,
            "current_milestone": "P2-M7c",
            "requirements": {"P2-R10.19": "P2-M7c"},
            "milestones": {
                "P2-M7c": {
                    "outcome": "Namespaced state works",
                    "status": "TODO",
                    "review_cycles": 0,
                    "review_override": None,
                    "baseline": {"commit": "base123", "branch": "fixture"},
                    "as_built": {"artifact": None, "result": "NOT_REQUIRED"},
                    "criteria": [
                        {
                            "id": "P2-M7c-AC1",
                            "status": "PENDING",
                            "text": "State changes safely",
                            "evidence": [],
                        }
                    ],
                    "tasks": [],
                    "reviews": [],
                    "findings": [],
                    "validation": [],
                    "follow_ups": [],
                }
            },
        }
        self.write_state()
        self.milestones_path.write_text(
            "# Milestones\n\n## P2-M7c — Namespaced state works\n\n"
            "Status: TODO\n\n### Acceptance Criteria\n\n"
            "- [ ] State changes safely\n\n### As-Built\n\nNOT_REQUIRED\n"
        )
        self.requirements_path.write_text(
            "# Requirements\n\n## Functional Requirements\n\n"
            "- [P2-R10.19] State changes safely\n\n## Constraints\n"
        )

    def write_state(self):
        self.state_path.write_text(json.dumps(self.state, indent=2) + "\n")

    def command(self, action, *extra):
        return subprocess.run(
            [
                sys.executable,
                str(TRANSITION),
                action,
                "--state",
                str(self.state_path),
                "--milestones",
                str(self.milestones_path),
                "--requirements",
                str(self.requirements_path),
                "--milestone",
                "P2-M7c",
                *map(str, extra),
            ],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def result(self, *, head="head456", verdict="PASS", complete=True):
        findings = []
        criterion_status = "PASS"
        if verdict == "CHANGES_REQUIRED":
            criterion_status = "FAIL"
            findings = [{
                "id": "F1", "severity": "IMPORTANT", "status": "OPEN",
                "summary": "Criterion is not yet proven",
            }]
        result = {
            "schema_version": 1,
            "milestone_id": "P2-M7c",
            "cycle": 1,
            "base": "base123",
            "head": head,
            "complete": complete,
            "verdict": verdict,
            "criteria": [{
                "id": "P2-M7c-AC1", "status": criterion_status,
                "evidence": ["pytest: pass" if criterion_status == "PASS" else "missing"],
            }],
            "findings": findings,
            "scope": "SUBSTANTIVE",
            "tier": "Mid",
            "model": "sonnet",
            "effort": "medium",
            "reason_code": "STANDARD_REVIEW",
        }
        if verdict == "CHANGES_REQUIRED":
            result["report_artifact"] = ".harness/reviews/P2-M7c-cycle1.md"
            (self.harness / "reviews" / "P2-M7c-cycle1.md").write_text("# Findings\n")
        return result

    def write_result(self, **overrides):
        path = self.harness / "reviews" / "P2-M7c-cycle1.result.json"
        path.write_text(json.dumps(self.result(**overrides), indent=2) + "\n")
        return path

    def test_pass_sequence_updates_json_and_markdown(self):
        entered = self.command("enter-review", "--head", "head456")
        self.assertEqual(entered.returncode, 0, entered.stderr)
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["milestones"]["P2-M7c"]["status"], "REVIEW")
        self.assertIn("Status: REVIEW", self.milestones_path.read_text())

        result_path = self.write_result()
        applied = self.command("apply-review", "--result", result_path)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        state = json.loads(self.state_path.read_text())
        milestone = state["milestones"]["P2-M7c"]
        self.assertEqual(milestone["criteria"][0]["status"], "PASS")
        self.assertEqual(milestone["reviews"][0]["result_artifact"],
                         ".harness/reviews/P2-M7c-cycle1.result.json")
        self.assertIn("- [x] State changes safely", self.milestones_path.read_text())

        finalized = self.command("finalize", "--head", "head456")
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["milestones"]["P2-M7c"]["status"], "DONE")
        self.assertIsNone(state["current_milestone"])
        checked = subprocess.run(
            [sys.executable, str(CHECK), str(self.state_path), "--milestones",
             str(self.milestones_path), "--requirements", str(self.requirements_path),
             "--all-done"],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_stale_or_incomplete_review_does_not_modify_state(self):
        self.assertEqual(self.command("enter-review", "--head", "head456").returncode, 0)
        before_state = self.state_path.read_text()
        before_milestones = self.milestones_path.read_text()
        for overrides in ({"head": "stale"}, {"complete": False}):
            path = self.write_result(**overrides)
            completed = self.command("apply-review", "--result", path)
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(self.state_path.read_text(), before_state)
            self.assertEqual(self.milestones_path.read_text(), before_milestones)

    def test_changes_required_reopens_and_counts_one_cycle(self):
        self.assertEqual(self.command("enter-review", "--head", "head456").returncode, 0)
        path = self.write_result(verdict="CHANGES_REQUIRED")
        completed = self.command("apply-review", "--result", path)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        milestone = json.loads(self.state_path.read_text())["milestones"]["P2-M7c"]
        self.assertEqual(milestone["status"], "IN_PROGRESS")
        self.assertEqual(milestone["review_cycles"], 1)
        self.assertIn("Status: IN_PROGRESS", self.milestones_path.read_text())

    def test_schema_v1_requires_explicit_upgrade(self):
        self.state["schema_version"] = 1
        self.write_state()
        before = self.state_path.read_text()
        completed = self.command("enter-review", "--head", "head456")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("require schema_version 2", completed.stderr)
        self.assertEqual(self.state_path.read_text(), before)


if __name__ == "__main__":
    unittest.main()
