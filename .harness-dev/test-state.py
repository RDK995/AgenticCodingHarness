#!/usr/bin/env python3
"""Black-box tests for structured state validation and migration."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check-state.py"
MIGRATE = ROOT / "scripts" / "migrate-state.py"


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = json.loads((ROOT / "examples" / "state.example.json").read_text())

    def write_state(self):
        path = self.root / "state.json"
        path.write_text(json.dumps(self.state))
        return path

    def run_check(self, *extra):
        return subprocess.run(
            [sys.executable, str(CHECK), str(self.write_state()), *map(str, extra)],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_valid_state_passes(self):
        self.assertEqual(self.run_check().returncode, 0)

    def test_done_requires_every_criterion_pass_and_no_open_finding(self):
        milestone = self.state["milestones"]["M1"]
        milestone["status"] = "DONE"
        milestone["findings"] = [{"id": "F1", "severity": "IMPORTANT", "status": "OPEN"}]
        completed = self.run_check()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not PASS", completed.stderr)
        self.assertIn("unresolved findings", completed.stderr)

    def test_cycle_override_must_be_named(self):
        self.state["milestones"]["M1"]["review_cycles"] = 3
        self.assertNotEqual(self.run_check().returncode, 0)
        self.state["milestones"]["M1"]["review_override"] = "human: one extra cycle"
        self.assertEqual(self.run_check().returncode, 0)

    def test_markdown_status_mismatch_fails(self):
        index = self.root / "milestones.md"
        index.write_text("# Milestones\n\n## M1 — Example\n\nStatus: DONE\n")
        completed = self.run_check("--milestones", index)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("index mismatch", completed.stderr)

    def test_all_done_is_a_mechanical_gate(self):
        self.state["current_milestone"] = None
        self.state["milestones"]["M1"]["status"] = "DONE"
        self.state["milestones"]["M1"]["criteria"][0]["status"] = "PASS"
        self.assertEqual(self.run_check("--all-done").returncode, 0)

    def test_all_done_requires_requirement_ownership(self):
        self.state["requirements"] = {}
        self.state["current_milestone"] = None
        self.state["milestones"]["M1"]["status"] = "DONE"
        self.state["milestones"]["M1"]["criteria"][0]["status"] = "PASS"
        completed = self.run_check("--all-done")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requirement ownership", completed.stderr)

    def test_record_only_gate_rejects_source_changes(self):
        harness = self.root / ".harness"
        harness.mkdir()
        self.state["milestones"]["M1"]["criteria"][0]["status"] = "PASS"
        state_path = harness / "state.json"
        state_path.write_text(json.dumps(self.state))
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "fixture@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Fixture"], check=True)
        (self.root / "source.py").write_text("before\n")
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "base"], check=True)
        base = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip()
        (self.root / "source.py").write_text("after\n")
        subprocess.run(["git", "-C", str(self.root), "add", "source.py"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "source"], check=True)
        head = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip()
        completed = subprocess.run(
            [sys.executable, str(CHECK), str(state_path), "--record-only", base, head],
            text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("substantive paths", completed.stderr)

    def test_migration_preserves_status_cycles_baseline_and_criteria(self):
        source = self.root / "milestones.md"
        target = self.root / "state.json"
        source.write_text(
            "# Milestones\n\n## M1 — Divide\n\nStatus: REVIEW\n\n"
            "### Acceptance Criteria\n\n- [x] quotient\n- [ ] zero\n\n"
            "### Baseline\n\nabc123 on m1-divide\n\n### Review Cycles\n\n1\n"
        )
        completed = subprocess.run(
            [sys.executable, str(MIGRATE), str(source), str(target)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        migrated = json.loads(target.read_text())
        milestone = migrated["milestones"]["M1"]
        self.assertEqual(milestone["status"], "REVIEW")
        self.assertEqual(milestone["review_cycles"], 1)
        self.assertEqual(milestone["baseline"]["branch"], "m1-divide")
        self.assertEqual(milestone["as_built"], {"artifact": None, "result": "PENDING"})
        self.assertEqual([item["status"] for item in milestone["criteria"]], ["PASS", "PENDING"])


if __name__ == "__main__":
    unittest.main()
