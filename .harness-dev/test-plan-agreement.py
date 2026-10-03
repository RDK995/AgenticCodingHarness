#!/usr/bin/env python3
"""Black-box tests for task-plan state: check-state.py's plan rules and
agree-plan.py, which records a human's agreement in all three places."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check-state.py"
AGREE = ROOT / "scripts" / "agree-plan.py"

INDEX = """# Milestones

## M1 — Calculator division is available

Status: TODO

### Outcome

### Architecture
N/A

### As-Built
N/A

### Acceptance Criteria
- [ ] Division returns the expected quotient

### Plan
`.harness/plans/M1.md` — DRAFT

### Baseline
abc1234 on m1-division

### Evidence

### Validation

### Review

### Review Cycles
0

### Follow-ups
"""

PLAN = """# M1 — Calculator division is available — task plan

Status: DRAFT

## Summary

Adds division.
"""


class PlanTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.harness = self.root / ".harness"
        (self.harness / "plans").mkdir(parents=True)
        (self.harness / "tasks").mkdir()
        (self.harness / "plans" / "M1.md").write_text(PLAN)
        (self.harness / "tasks" / "M1-T1.md").write_text("# packet\n")
        self.index = self.harness / "milestones.md"
        self.index.write_text(INDEX)
        self.requirements = self.harness / "requirements.md"
        self.requirements.write_text(
            "# Requirements\n\n## Functional Requirements\n\n"
            "- [FR1] Divide numbers\n- [FR2] Reject division by zero\n\n"
            "## Acceptance Criteria\n"
        )
        self.state = json.loads((ROOT / "examples" / "state.example.json").read_text())
        milestone = self.state["milestones"]["M1"]
        milestone["plan"] = {"status": "DRAFT", "artifact": ".harness/plans/M1.md"}
        milestone["tasks"][0]["artifact"] = ".harness/tasks/M1-T1.md"
        self.state_path = self.harness / "state.json"
        self.write_state()

    def write_state(self):
        self.state_path.write_text(json.dumps(self.state))

    def invoke(self, script, *args):
        return subprocess.run(
            [sys.executable, str(script), *map(str, args)],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def check(self):
        self.write_state()
        return self.invoke(CHECK, self.state_path, "--milestones", self.index)

    def agree(self):
        self.write_state()
        return self.invoke(
            AGREE, self.state_path, "M1",
            "--milestones", self.index, "--requirements", self.requirements,
        )

    # check-state.py

    def test_draft_plan_is_valid_state(self):
        self.assertEqual(self.check().returncode, 0, self.check().stderr)

    def test_a_milestone_without_a_plan_is_still_valid(self):
        del self.state["milestones"]["M1"]["plan"]
        self.assertEqual(self.check().returncode, 0)

    def test_unknown_plan_status_fails(self):
        self.state["milestones"]["M1"]["plan"]["status"] = "APPROVED"
        completed = self.check()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("plan.status is invalid", completed.stderr)

    def test_plan_must_name_an_existing_file(self):
        self.state["milestones"]["M1"]["plan"]["artifact"] = ".harness/plans/M9.md"
        completed = self.check()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("plan names missing artifact", completed.stderr)

    def test_agreed_plan_needs_tasks(self):
        self.state["milestones"]["M1"]["plan"]["status"] = "AGREED"
        self.state["milestones"]["M1"]["tasks"] = []
        completed = self.check()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("AGREED with no tasks", completed.stderr)

    # agree-plan.py

    def test_agreeing_sets_all_three_records(self):
        completed = self.agree()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["milestones"]["M1"]["plan"]["status"], "AGREED")
        self.assertIn("Status: AGREED", (self.harness / "plans" / "M1.md").read_text())
        index = self.index.read_text()
        self.assertIn("### Plan\n`.harness/plans/M1.md` — AGREED\n\n### Baseline", index)
        self.assertNotIn("DRAFT", index)
        # Everything outside the Plan field is untouched.
        self.assertEqual(index.replace("— AGREED", "— DRAFT"), INDEX)

    def test_index_without_a_plan_field_gets_one_before_baseline(self):
        self.index.write_text(INDEX.replace("### Plan\n`.harness/plans/M1.md` — DRAFT\n\n", ""))
        completed = self.agree()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.index.read_text().replace("— AGREED", "— DRAFT"), INDEX)

    def test_refuses_a_plan_that_is_not_draft(self):
        self.state["milestones"]["M1"]["plan"]["status"] = "AGREED"
        completed = self.agree()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("no DRAFT plan", completed.stderr)

    def test_refuses_a_milestone_already_under_way(self):
        self.state["milestones"]["M1"]["status"] = "IN_PROGRESS"
        self.index.write_text(INDEX.replace("Status: TODO", "Status: IN_PROGRESS"))
        completed = self.agree()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not TODO", completed.stderr)

    def test_refuses_a_task_without_a_packet_and_writes_nothing(self):
        (self.harness / "tasks" / "M1-T1.md").unlink()
        completed = self.agree()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("has no packet on disk", completed.stderr)
        self.assertEqual(json.loads(self.state_path.read_text())["milestones"]["M1"]["plan"]["status"], "DRAFT")
        self.assertIn("Status: DRAFT", (self.harness / "plans" / "M1.md").read_text())
        self.assertEqual(self.index.read_text(), INDEX)

    def test_refuses_when_state_is_inconsistent_and_writes_nothing(self):
        self.index.write_text(INDEX.replace("Status: TODO", "Status: REVIEW"))
        completed = self.agree()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("index mismatch", completed.stderr)
        self.assertIn("Status: DRAFT", (self.harness / "plans" / "M1.md").read_text())


if __name__ == "__main__":
    unittest.main()
