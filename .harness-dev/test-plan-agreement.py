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

    # several milestones at once

    def add_m2(self, status="TODO", plan="DRAFT"):
        import copy
        m2 = copy.deepcopy(self.state["milestones"]["M1"])
        m2["status"] = status
        m2["criteria"][0]["id"] = "M2-AC1"
        m2["tasks"][0].update(id="M2-T1", artifact=".harness/tasks/M2-T1.md")
        m2["plan"] = {"status": plan, "artifact": ".harness/plans/M2.md"}
        self.state["milestones"]["M2"] = m2
        (self.harness / "plans" / "M2.md").write_text(PLAN.replace("M1", "M2"))
        (self.harness / "tasks" / "M2-T1.md").write_text("# packet\n")
        section = INDEX.split("\n", 2)[2].replace("M1", "M2").replace("Status: TODO", f"Status: {status}")
        self.index.write_text(INDEX + "\n" + section)

    def agree_ids(self, *ids):
        self.write_state()
        return self.invoke(
            AGREE, self.state_path, *ids,
            "--milestones", self.index, "--requirements", self.requirements,
        )

    def test_agrees_several_plans_in_one_call(self):
        self.add_m2()
        completed = self.agree_ids("M1", "M2")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        state = json.loads(self.state_path.read_text())
        self.assertEqual([state["milestones"][m]["plan"]["status"] for m in ("M1", "M2")], ["AGREED", "AGREED"])
        self.assertIn("Status: AGREED", (self.harness / "plans" / "M2.md").read_text())
        self.assertEqual(self.index.read_text().count("— AGREED"), 2)

    def test_refuses_a_later_plan_ahead_of_an_unagreed_earlier_one(self):
        self.add_m2()
        completed = self.agree_ids("M2")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("cannot agree M2 before M1", completed.stderr)
        self.assertIn("Status: DRAFT", (self.harness / "plans" / "M2.md").read_text())

    def test_a_milestone_already_under_way_does_not_hold_back_later_plans(self):
        self.state["milestones"]["M1"]["status"] = "IN_PROGRESS"
        self.add_m2()
        self.index.write_text(self.index.read_text().replace("Status: TODO", "Status: IN_PROGRESS", 1))
        completed = self.agree_ids("M2")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_one_bad_milestone_writes_nothing_for_any(self):
        self.add_m2()
        (self.harness / "tasks" / "M2-T1.md").unlink()
        completed = self.agree_ids("M1", "M2")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Status: DRAFT", (self.harness / "plans" / "M1.md").read_text())
        self.assertNotIn("AGREED", self.index.read_text())



class OwnershipTests(unittest.TestCase):
    """Creating milestones belongs to plan-milestone; implement only runs them."""

    def test_implement_no_longer_creates_milestones(self):
        implement = (ROOT / "skills/implement/SKILL.md").read_text()
        self.assertNotIn("generate milestones", implement)
        self.assertNotIn("migrate-state.py", implement)
        self.assertIn("STOP — tell the human to run /harness:plan-milestone", implement)

    def test_plan_milestone_creates_then_plans(self):
        plan = (ROOT / "skills/plan-milestone/SKILL.md").read_text()
        self.assertLess(plan.index("CREATE THE MILESTONES"), plan.index("SCOPE —"))
        self.assertIn("generate\n    milestones", plan)
        self.assertIn("migrate-state.py", plan)


if __name__ == "__main__":
    unittest.main()
