#!/usr/bin/env python3
"""Black-box tests for the implement-loop stop conditions.

A fake `claude` on PATH stands in for each headless session. Each call takes the
next scripted step: set milestone statuses in .harness/state.json, optionally
commit, print something, and exit with a given status.
"""

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "scripts" / "implement-loop.py"

FAKE_CLAUDE = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json, os, subprocess, sys
    from pathlib import Path
    script = Path(os.environ["FAKE_CLAUDE_SCRIPT"])
    steps = json.loads(script.read_text())
    calls = Path(os.environ["FAKE_CLAUDE_CALLS"])
    with calls.open("a") as handle:
        handle.write(json.dumps(sys.argv[1:]) + "\\n")
    step = steps.pop(0) if steps else {}
    script.write_text(json.dumps(steps))
    state_path = Path(".harness/state.json")
    if step.get("set"):
        state = json.loads(state_path.read_text())
        for milestone, status in step["set"].items():
            state["milestones"].setdefault(milestone, {})["status"] = status
        state_path.write_text(json.dumps(state, indent=2))
    if step.get("commit"):
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-qm", "fake step", "--allow-empty"], check=True)
    print(step.get("say", "fake session output"))
    sys.exit(step.get("exit", 0))
    """
)


class ImplementLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.project = base / "project"
        (self.project / ".harness").mkdir(parents=True)
        self.bin = base / "bin"
        self.bin.mkdir()
        fake = self.bin / "claude"
        fake.write_text(FAKE_CLAUDE)
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        self.script = base / "steps.json"
        self.calls = base / "calls.jsonl"
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "test")

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.project, check=True, text=True, capture_output=True
        ).stdout.strip()

    def seed(self, statuses):
        state = {
            "schema_version": 1,
            "current_milestone": None,
            "milestones": {key: {"status": value} for key, value in statuses.items()},
        }
        (self.project / ".harness" / "state.json").write_text(json.dumps(state, indent=2))
        self.git("add", "-A")
        self.git("commit", "-qm", "baseline")

    def run_loop(self, steps, *args):
        self.script.write_text(json.dumps(steps))
        env = {
            **os.environ,
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "FAKE_CLAUDE_SCRIPT": str(self.script),
            "FAKE_CLAUDE_CALLS": str(self.calls),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        return subprocess.run(
            [sys.executable, str(LOOP), *args],
            cwd=self.project,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def call_count(self):
        return len(self.calls.read_text().splitlines()) if self.calls.exists() else 0

    def statuses(self):
        state = json.loads((self.project / ".harness" / "state.json").read_text())
        return {key: value["status"] for key, value in state["milestones"].items()}

    def test_runs_until_every_milestone_is_done(self):
        self.seed({"M1": "TODO", "M2": "TODO"})
        completed = self.run_loop(
            [
                {"set": {"M1": "REVIEW"}, "commit": True},
                {"set": {"M1": "DONE"}, "commit": True},
                {"set": {"M2": "DONE"}, "commit": True},
            ]
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(self.call_count(), 3)
        lines = completed.stdout.splitlines()
        self.assertIn("[1] M1: TODO -> REVIEW, HEAD ", lines[0])
        self.assertIn("[2] M1: REVIEW -> DONE", lines[1])
        self.assertIn("[3] M2: TODO -> DONE", lines[2])
        self.assertEqual(lines[-1], "STOP: all milestones are DONE")

    def test_already_done_runs_nothing(self):
        self.seed({"M1": "DONE"})
        completed = self.run_loop([])
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(self.call_count(), 0)

    def test_stops_when_selected_milestone_becomes_blocked(self):
        self.seed({"M1": "TODO", "M2": "TODO"})
        completed = self.run_loop([{"set": {"M1": "BLOCKED"}, "commit": True}])
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 1)
        self.assertIn("M1 is BLOCKED", completed.stdout)

    def test_blocked_before_start_runs_nothing_and_never_skips_ahead(self):
        self.seed({"M1": "DONE", "M2": "BLOCKED", "M3": "TODO"})
        completed = self.run_loop([])
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 0)
        self.assertIn("M2 is BLOCKED", completed.stdout)

    def test_status_without_an_implement_step_stops(self):
        self.seed({"M1": "DEFERRED", "M2": "TODO"})
        completed = self.run_loop([])
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 0)
        self.assertIn("DEFERRED", completed.stdout)

    def test_no_progress_stops(self):
        self.seed({"M1": "REVIEW"})
        completed = self.run_loop([{"say": "waiting for a human live check"}, {}])
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 1)
        self.assertIn("changed neither", completed.stdout)

    def test_state_change_without_commit_counts_as_progress(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([{"set": {"M1": "IN_PROGRESS"}}, {"set": {"M1": "DONE"}}])
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(self.call_count(), 2)

    def test_commit_without_state_change_counts_as_progress(self):
        self.seed({"M1": "IN_PROGRESS"})
        completed = self.run_loop([{"commit": True}, {"set": {"M1": "DONE"}}])
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(self.call_count(), 2)

    def test_until_stops_before_running_that_milestone(self):
        self.seed({"M1": "TODO", "M2": "TODO", "M3": "TODO"})
        completed = self.run_loop(
            [{"set": {"M1": "DONE"}, "commit": True}, {"set": {"M2": "DONE"}}], "--until", "M2"
        )
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 1)
        self.assertEqual(self.statuses()["M2"], "TODO")
        self.assertIn("reached --until M2", completed.stdout)

    def test_until_rejects_unknown_or_done_milestone(self):
        self.seed({"M1": "DONE", "M2": "TODO"})
        for target in ("M9", "M1"):
            with self.subTest(target=target):
                completed = self.run_loop([], "--until", target)
                self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.call_count(), 0)

    def test_max_iterations(self):
        self.seed({"M1": "TODO", "M2": "TODO", "M3": "TODO"})
        completed = self.run_loop(
            [{"set": {"M1": "DONE"}, "commit": True}, {"set": {"M2": "DONE"}, "commit": True}],
            "--max",
            "2",
        )
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 2)
        self.assertIn("reached --max 2", completed.stdout)

    def test_nonzero_claude_exit_is_an_error(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([{"set": {"M1": "IN_PROGRESS"}, "exit": 7}])
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.call_count(), 1)
        self.assertIn("exited with status 7", completed.stdout)

    def test_logs_each_iteration_and_keeps_them_out_of_git(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([{"set": {"M1": "DONE"}, "commit": True, "say": "SESSION-MARKER"}])
        self.assertEqual(completed.returncode, 0)
        logs = sorted((self.project / ".harness/evidence/implement-loop").glob("*-1.log"))
        self.assertEqual(len(logs), 1)
        self.assertRegex(logs[0].name, r"^\d{8}T\d{6}Z-1\.log$")
        self.assertIn("SESSION-MARKER", logs[0].read_text())
        self.assertNotIn("SESSION-MARKER", completed.stdout)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_passes_headless_flags_and_safe_default_permission_mode(self):
        self.seed({"M1": "TODO"})
        self.run_loop([{"set": {"M1": "DONE"}}], "--plugin-dir", "/plugins/harness")
        argv = json.loads(self.calls.read_text().splitlines()[0])
        self.assertEqual(argv[:2], ["-p", "/harness:implement"])
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "acceptEdits")
        self.assertEqual(argv[argv.index("--permission-prompts") + 1], "none")
        self.assertEqual(argv[argv.index("--plugin-dir") + 1], "/plugins/harness")
        self.assertNotIn("--dangerously-skip-permissions", argv)

    def test_permission_mode_passthrough(self):
        self.seed({"M1": "TODO"})
        self.run_loop([{"set": {"M1": "DONE"}}], "--permission-mode", "dontAsk")
        argv = json.loads(self.calls.read_text().splitlines()[0])
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "dontAsk")

    def test_missing_state_is_an_error(self):
        completed = self.run_loop([])
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.call_count(), 0)


if __name__ == "__main__":
    unittest.main()
