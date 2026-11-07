#!/usr/bin/env python3
"""Black-box tests for the unattended loop driver's start/status/stop lifecycle."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "implement-loop.py"

STATE = {
    "schema_version": 1,
    "current_milestone": "M2",
    "milestones": {
        "M1": {"outcome": "first", "status": "DONE"},
        "M2": {"outcome": "second", "status": "IN_PROGRESS"},
        "M3": {"outcome": "third", "status": "TODO"},
    },
}

SLEEPING_CLAUDE = '#!/bin/sh\necho "$@" > "{args}"\nsleep 60\n'
STUBBORN_CLAUDE = '#!/bin/sh\ntrap "" TERM\necho "$@" > "{args}"\nsleep 60\n'
QUICK_CLAUDE = '#!/bin/sh\necho "$@" > "{args}"\nexit 0\n'


def wait_for(predicate, timeout=10.0, interval=0.05):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    return predicate()


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def group_alive(pgid):
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def process_table():
    output = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,command="], text=True, capture_output=True, check=True
    ).stdout
    rows = []
    for line in output.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3:
            rows.append((int(parts[0]), int(parts[1]), parts[2]))
    return rows


class ImplementLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.project = base / "project"
        self.tools = base / "tools"
        self.project.mkdir()
        self.tools.mkdir()
        self.loop = self.project / ".harness" / "loop"
        self.notify = self.tools / "notifications.txt"
        self.args_file = self.tools / "claude-args.txt"
        (self.project / ".harness").mkdir()
        (self.project / ".harness" / "state.json").write_text(json.dumps(STATE, indent=2))
        (self.project / "README.md").write_text("fixture\n")
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "init")
        self.pids = []
        self.groups = []
        self.addCleanup(self.kill_started)

    def kill_started(self):
        for pgid in self.groups:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        for pid in self.pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.project, text=True, capture_output=True, check=True
        ).stdout

    def fake_claude(self, body):
        path = self.tools / "claude"
        path.write_text(body.format(args=self.args_file))
        path.chmod(0o755)
        return path

    def run_loop(self, command, *extra, timeout=60):
        env = os.environ.copy()
        env.pop("HARNESS_LOOP_CLAUDE", None)
        return subprocess.run(
            [sys.executable, str(SCRIPT), command, "--project", str(self.project), *extra],
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout,
            check=False,
        )

    def start(self, claude, *extra):
        began = time.monotonic()
        result = self.run_loop(
            "start", "--claude", str(claude), "--notify-file", str(self.notify), *extra
        )
        elapsed = time.monotonic() - began
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result, elapsed

    def driver_pid(self):
        pid = int((self.loop / "driver.pid").read_text().strip())
        if pid not in self.pids:
            self.pids.append(pid)
        return pid

    def current_step(self):
        path = self.loop / "current-step.json"
        if not path.exists():
            return None
        try:
            step = json.loads(path.read_text())
        except json.JSONDecodeError:
            return None
        if step["pid"] not in self.groups:
            self.groups.append(step["pid"])
        return step

    def notifications(self):
        if not self.notify.exists():
            return []
        return [line for line in self.notify.read_text().splitlines() if line.strip()]

    def start_running(self, body, *extra):
        result, elapsed = self.start(self.fake_claude(body), *extra)
        self.assertTrue((self.loop / "driver.pid").exists(), "start returned before driver.pid")
        pid = self.driver_pid()
        step = wait_for(self.current_step)
        self.assertIsNotNone(step, "current-step.json never appeared")
        self.assertTrue(wait_for(self.args_file.exists), "fake claude never ran")
        return result, elapsed, pid, step

    def test_start_detaches_driver_and_status_reports_it(self):
        _, elapsed, pid, step = self.start_running(SLEEPING_CLAUDE)
        self.assertLess(elapsed, 5.0)

        table = {row[0]: row for row in process_table()}
        self.assertIn(pid, table)
        self.assertNotEqual(table[pid][1], os.getpid(), "driver must not be a child of the invoker")
        self.assertNotEqual(os.getsid(pid), os.getsid(0), "driver must run in its own session")
        self.assertEqual(os.getsid(pid), pid, "driver must lead its own session")

        caffeinate = [
            row for row in table.values()
            if "caffeinate" in row[2] and row[2].split()[-2:] == ["-w", str(pid)]
        ]
        self.assertEqual(len(caffeinate), 1, "expected one `caffeinate -w <driver pid>` process")
        self.assertEqual(caffeinate[0][1], pid, "caffeinate must be started by the driver")

        self.assertEqual(step["step"], 1)
        self.assertEqual(step["milestone"], "M2")
        self.assertEqual(step["attempt"], 1)
        self.assertIn("started", step)
        self.assertNotEqual(os.getsid(step["pid"]), pid, "step must run in its own session")
        self.assertEqual(self.args_file.read_text().split(), ["-p", "/harness:implement"])

        status = self.run_loop("status")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertIn("running", status.stdout)
        self.assertNotIn("not running", status.stdout)
        self.assertIn(str(pid), status.stdout)
        self.assertRegex(status.stdout, r"step\D*1\b")
        self.assertIn("M2", status.stdout)

        log = (self.loop / "loop.log").read_text()
        self.assertIn("driver started", log)
        self.assertIn("caffeinate", log)
        self.assertIn(str(step["pid"]), log)

    def test_stop_ends_step_and_driver_leaving_log_and_git_untouched(self):
        head = self.git("rev-parse", "HEAD")
        _, _, pid, step = self.start_running(SLEEPING_CLAUDE)
        porcelain = self.git("status", "--porcelain")

        stop = self.run_loop("stop")
        self.assertEqual(stop.returncode, 0, stop.stdout + stop.stderr)
        self.assertIn("stopped", stop.stdout)

        self.assertFalse(alive(pid), "driver still alive after stop returned")
        self.assertTrue(wait_for(lambda: not group_alive(step["pid"]), 5), "step group still alive")
        self.assertFalse((self.loop / "driver.pid").exists())
        self.assertTrue((self.loop / "loop.log").exists())
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.git("status", "--porcelain"), porcelain)
        self.assertEqual(porcelain, "", "loop state must not dirty the working tree")
        outcome = json.loads((self.loop / "outcome.json").read_text())
        self.assertEqual(outcome["outcome"], "stopped by owner")
        self.assertEqual(outcome["milestone"], "M2")
        self.assertEqual(len(self.notifications()), 1, self.notifications())
        self.assertFalse(
            [row for row in process_table() if row[2].split()[-2:] == ["-w", str(pid)]],
            "caffeinate outlived the driver",
        )

        status = self.run_loop("status")
        self.assertEqual(status.returncode, 0)
        self.assertIn("not running", status.stdout)

    def test_stop_kills_step_that_ignores_sigterm_after_grace(self):
        _, _, pid, step = self.start_running(STUBBORN_CLAUDE, "--grace", "1")

        began = time.monotonic()
        stop = self.run_loop("stop")
        elapsed = time.monotonic() - began
        self.assertEqual(stop.returncode, 0, stop.stdout + stop.stderr)
        self.assertGreaterEqual(elapsed, 0.9, "the grace period was not honoured")
        self.assertLess(elapsed, 15.0)

        self.assertFalse(alive(pid))
        self.assertTrue(wait_for(lambda: not group_alive(step["pid"]), 5), "step group still alive")
        self.assertFalse((self.loop / "driver.pid").exists())
        self.assertIn("SIGKILL", (self.loop / "loop.log").read_text())
        self.assertEqual(len(self.notifications()), 1, self.notifications())

    def test_status_and_stop_report_not_running_without_live_driver(self):
        for command in ("status", "stop"):
            with self.subTest(case="no pid file", command=command):
                result = self.run_loop(command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("not running", result.stdout)

        dead = subprocess.Popen(["true"])
        dead.wait()
        for label, pid in (("dead pid", dead.pid), ("pid of another process", os.getpid())):
            for command in ("status", "stop"):
                with self.subTest(case=label, command=command):
                    self.loop.mkdir(parents=True, exist_ok=True)
                    (self.loop / "driver.pid").write_text(f"{pid}\n")
                    result = self.run_loop(command)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("not running", result.stdout)
                    self.assertTrue(alive(os.getpid()))
        self.assertEqual(self.notifications(), [])

    def test_driver_ends_by_itself_after_one_step(self):
        claude = self.fake_claude(QUICK_CLAUDE)
        _, elapsed = self.start(claude)
        self.assertLess(elapsed, 5.0)

        self.assertTrue(
            wait_for(lambda: (self.loop / "outcome.json").exists() and not (self.loop / "driver.pid").exists()),
            "driver did not finish by itself",
        )
        outcome = json.loads((self.loop / "outcome.json").read_text())
        self.assertEqual(outcome["outcome"], "finished one step")
        self.assertEqual(outcome["milestone"], "M2")
        self.assertIn("time", outcome)
        self.assertEqual(self.args_file.read_text().split(), ["-p", "/harness:implement"])
        self.assertTrue(wait_for(lambda: len(self.notifications()) == 1, 2))
        self.assertEqual(len(self.notifications()), 1, self.notifications())
        self.assertTrue((self.loop / "step-1.out").exists())
        self.assertIn("finished one step", (self.loop / "loop.log").read_text())

        status = self.run_loop("status")
        self.assertEqual(status.returncode, 0)
        self.assertIn("not running", status.stdout)

    def test_no_sink_records_unsent_notification_in_log(self):
        claude = self.fake_claude(QUICK_CLAUDE)
        result = self.run_loop("start", "--claude", str(claude))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(
            wait_for(lambda: (self.loop / "outcome.json").exists() and not (self.loop / "driver.pid").exists())
        )
        self.assertIn("not sent: no sink configured", (self.loop / "loop.log").read_text())


if __name__ == "__main__":
    unittest.main()
