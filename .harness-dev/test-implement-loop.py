#!/usr/bin/env python3
"""Black-box tests for the unattended loop driver's start/status/stop lifecycle."""

import importlib.util
import json
import os
from pathlib import Path
import re
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
# Records argv one per line and the environment it was given. /bin/sh itself
# adds PWD, SHLVL and _ to what it exports, so those are dropped before recording.
RECORDING_CLAUDE = (
    '#!/bin/sh\nprintf "%s\\n" "$@" > "{args}.tmp"\n'
    'env -u PWD -u SHLVL -u _ > "{args}.env"\nmv "{args}.tmp" "{args}"\nexit 0\n'
)
ALLOWED_ENV = {
    "PATH", "HOME", "USER", "GIT_TERMINAL_PROMPT",
    "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "CLAUDE_CONFIG_DIR",
}
REQUIRED_DENY = [
    "Bash(git push:*)",
    "Bash(git merge:*)",
    "Bash(git rebase:*)",
    "Bash(git reset --hard:*)",
    "Bash(git commit --amend:*)",
    "Bash(git filter-branch:*)",
    "Bash(git checkout main:*)",
    "Bash(git checkout master:*)",
    "Bash(git switch main:*)",
    "Bash(git switch master:*)",
    "Bash(git branch -f:*)",
    "Bash(git update-ref:*)",
]
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2} ")


def load_script():
    spec = importlib.util.spec_from_file_location("implement_loop", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    def run_loop(self, command, *extra, timeout=60, extra_env=None):
        env = os.environ.copy()
        env.pop("HARNESS_LOOP_CLAUDE", None)
        env.update(extra_env or {})
        return subprocess.run(
            [sys.executable, str(SCRIPT), command, "--project", str(self.project), *extra],
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout,
            check=False,
        )

    def start(self, claude, *extra, extra_env=None):
        began = time.monotonic()
        result = self.run_loop(
            "start", "--claude", str(claude), "--notify-file", str(self.notify), *extra,
            extra_env=extra_env,
        )
        elapsed = time.monotonic() - began
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result, elapsed

    def assert_prompt_argument(self, argv):
        self.assertIn("-p", argv)
        self.assertEqual(argv[argv.index("-p") + 1], "/harness:implement")

    def assert_locked_down(self, argv):
        """The step command line carries every lockdown flag and the same deny rules twice."""
        self.assert_prompt_argument(argv)

        def value_of(flag):
            self.assertIn(flag, argv)
            return argv[argv.index(flag) + 1]

        self.assertEqual(value_of("--permission-mode"), "bypassPermissions")
        self.assertEqual(value_of("--permission-prompts"), "none")
        self.assertEqual(Path(value_of("--plugin-dir")), ROOT)
        settings = json.loads(value_of("--settings"))
        deny = settings["permissions"]["deny"]
        for rule in REQUIRED_DENY:
            self.assertIn(rule, deny)
        start = argv.index("--disallowedTools") + 1
        self.assertEqual(argv[start:start + len(deny)], deny)
        return deny

    def run_recording_step(self, extra_env=None):
        self.start(self.fake_claude(RECORDING_CLAUDE), extra_env=extra_env)
        finished = wait_for(
            lambda: (self.loop / "outcome.json").exists() and not (self.loop / "driver.pid").exists()
        )
        self.assertTrue(finished, "driver did not finish by itself")
        self.assertTrue(self.args_file.exists(), "fake claude never ran")
        argv = self.args_file.read_text().splitlines()
        env = dict(
            line.split("=", 1)
            for line in Path(f"{self.args_file}.env").read_text().splitlines()
            if "=" in line
        )
        return argv, env

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
        self.assert_prompt_argument(self.args_file.read_text().split())

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
        self.assertEqual(outcome["outcome"], "failed step: no state progress")
        self.assertEqual(outcome["milestone"], "M2")
        self.assertIn("time", outcome)
        self.assert_prompt_argument(self.args_file.read_text().split())
        self.assertTrue(wait_for(lambda: len(self.notifications()) == 1, 2))
        self.assertEqual(len(self.notifications()), 1, self.notifications())
        self.assertTrue((self.loop / "step-1.out").exists())
        self.assertIn("failed step: no state progress", (self.loop / "loop.log").read_text())

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

    def run_quick_step(self, notify=True):
        claude = self.fake_claude(QUICK_CLAUDE)
        if notify:
            self.start(claude)
        else:
            result = self.run_loop("start", "--claude", str(claude))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        finished = wait_for(
            lambda: (self.loop / "outcome.json").exists() and not (self.loop / "driver.pid").exists()
        )
        self.assertTrue(finished, "driver did not finish by itself")

    def loop_log_matches(self, fragment):
        lines = [line for line in (self.loop / "loop.log").read_text().splitlines() if fragment in line]
        self.assertTrue(lines, f"no loop.log line contains {fragment!r}")
        for line in lines:
            self.assertRegex(line, TIMESTAMP, f"loop.log line lacks a timestamp: {line}")
        return lines

    def test_loop_log_records_step_lifecycle_with_timestamps(self):
        self.run_quick_step()

        self.loop_log_matches("step 1 started: milestone M2, attempt 1")
        self.loop_log_matches("step 1 outcome: failed step: no state progress")
        self.loop_log_matches("notification sent")
        self.loop_log_matches("final outcome: failed step: no state progress")

    def test_loop_log_records_unsent_notification_without_notify_file(self):
        self.run_quick_step(notify=False)

        self.loop_log_matches("notification not sent")

    def test_commands_log_records_children_with_prompt_by_length(self):
        self.run_quick_step()

        commands_path = self.loop / "commands.log"
        self.assertTrue(commands_path.exists(), "commands.log was not written")
        commands = commands_path.read_text()
        step = json.loads((self.loop / "current-step.json").read_text())
        driver = int(re.search(r"driver started: pid (\d+)", (self.loop / "loop.log").read_text()).group(1))

        step_lines = [line for line in commands.splitlines() if f" pid {step['pid']}: " in line]
        self.assertEqual(len(step_lines), 1, commands)
        self.assertIn(str(self.tools / "claude"), step_lines[0])
        self.assertIn("-p <prompt: 18 chars>", step_lines[0])

        caffeinate_lines = [line for line in commands.splitlines() if line.endswith(f"caffeinate -w {driver}")]
        self.assertEqual(len(caffeinate_lines), 1, commands)

        for name in ("commands.log", "loop.log"):
            self.assertNotIn("/harness:implement", (self.loop / name).read_text(), name)

    def test_git_add_stages_fixture_changes_but_never_loop_state(self):
        (self.project / ".harness" / "note.md").write_text("new note\n")
        state = self.project / ".harness" / "state.json"
        state.write_text(state.read_text() + "\n")
        self.run_quick_step()
        self.assertTrue((self.loop / "loop.log").exists())

        self.git("add", ".harness")
        staged = self.git("diff", "--cached", "--name-only").splitlines()

        self.assertIn(".harness/note.md", staged)
        self.assertIn(".harness/state.json", staged)
        self.assertEqual([path for path in staged if path.startswith(".harness/loop/")], [])

    def test_builder_returns_locked_down_command(self):
        module = load_script()
        command, env = module.session_command("/bin/claude", "/harness:implement", {"PATH": "/usr/bin"})
        self.assertEqual(command[0], "/bin/claude")
        deny = self.assert_locked_down(command[1:])
        self.assertEqual(deny, list(module.DENY_RULES))
        self.assertEqual(env, {"PATH": "/usr/bin", "GIT_TERMINAL_PROMPT": "0"})

    def test_builder_takes_the_prompt_as_a_parameter(self):
        module = load_script()
        command, _ = module.session_command("claude", "say ok", {})
        self.assertEqual(command[command.index("-p") + 1], "say ok")

    def test_step_runs_locked_down_with_minimal_environment(self):
        argv, env = self.run_recording_step()

        self.assert_locked_down(argv)
        self.assertLessEqual(set(env), ALLOWED_ENV, sorted(set(env) - ALLOWED_ENV))
        self.assertIn("PATH", env)
        self.assertIn("HOME", env)
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")

    def test_parent_secret_reaches_neither_step_nor_logs(self):
        argv, env = self.run_recording_step(
            {"HARNESS_FAKE_SECRET": "s3cr3t-value-123", "ANTHROPIC_API_KEY": "sk-fake-key-456"}
        )

        self.assertNotIn("HARNESS_FAKE_SECRET", set(env))
        leaked = [name for name, value in env.items() if "s3cr3t-value-123" in value]
        self.assertEqual(leaked, [], "the parent secret reached the step environment")
        self.assertEqual(env.get("ANTHROPIC_API_KEY"), "sk-fake-key-456", "sign-in value must pass through")
        for name in ("commands.log", "loop.log"):
            text = (self.loop / name).read_text()
            for secret in ("s3cr3t-value-123", "sk-fake-key-456"):
                self.assertFalse(secret in text, f"{secret} leaked into {name}")

    def test_driver_source_runs_no_push_or_merge(self):
        source = SCRIPT.read_text()
        without_rules = re.sub(r'"Bash\([^"]*\)"', '""', source)
        self.assertTrue("DENY_RULES" in source, "deny rules constant not found")
        self.assertNotRegex(without_rules, r"""["'](push|merge)["']""")
        self.assertNotRegex(without_rules, r"git\s+(push|merge)")

    # --- M2-T2: successive fresh steps judged from recorded state ---
    def write_state(self, statuses, current=None):
        state = {
            "schema_version": 1,
            "current_milestone": current or next(iter(statuses)),
            "milestones": {name: {"outcome": name, "status": status} for name, status in statuses.items()},
        }
        (self.project / ".harness" / "state.json").write_text(json.dumps(state, indent=2))

    def scripted_claude(self, plan):
        """A fake claude that records each run, then applies plan[run] (the last entry repeats)."""
        runs = self.tools / "runs.jsonl"
        body = (
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            f"runs = Path({str(runs)!r})\n"
            f"plan = {plan!r}\n"
            "with open(runs, 'a') as handle:\n"
            "    handle.write(json.dumps({'pid': os.getpid(), 'cwd': os.getcwd(), 'argv': sys.argv[1:]}) + '\\n')\n"
            "number = len(runs.read_text().splitlines())\n"
            "step = plan[min(number, len(plan)) - 1]\n"
            "if 'statuses' in step:\n"
            "    names = list(step['statuses'])\n"
            "    state = {'schema_version': 1, 'current_milestone': step.get('current', names[0]),\n"
            "             'milestones': {n: {'outcome': n, 'status': step['statuses'][n]} for n in names}}\n"
            "    Path('.harness/state.json').write_text(json.dumps(state, indent=2))\n"
            "if 'notes' in step:\n"
            "    Path('.harness/milestones.md').write_text(step['notes'])\n"
            "print(step.get('print', ''))\n"
            "sys.exit(step.get('exit', 0))\n"
        )
        path = self.tools / "claude"
        path.write_text(body)
        path.chmod(0o755)
        return path

    def recorded_runs(self):
        path = self.tools / "runs.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines()]

    def run_to_end(self, plan):
        self.start(self.scripted_claude(plan))
        finished = wait_for(
            lambda: (self.loop / "outcome.json").exists() and not (self.loop / "driver.pid").exists(),
            timeout=30,
        )
        self.assertTrue(finished, "driver did not finish by itself")
        outcome = json.loads((self.loop / "outcome.json").read_text())["outcome"]
        self.assertTrue(wait_for(lambda: len(self.notifications()) == 1, 2))
        self.assertEqual(len(self.notifications()), 1, self.notifications())
        return outcome

    def test_loop_runs_successive_fresh_steps_until_every_milestone_is_done(self):
        self.write_state({"M1": "TODO", "M2": "TODO"})
        plan = [
            {"statuses": {"M1": "REVIEW", "M2": "TODO"}},
            {"statuses": {"M1": "DONE", "M2": "TODO"}, "current": "M2"},
            {"statuses": {"M1": "DONE", "M2": "REVIEW"}, "current": "M2"},
            {"statuses": {"M1": "DONE", "M2": "DONE"}, "current": "M2"},
        ]
        self.assertEqual(self.run_to_end(plan), "finished: every milestone is DONE")

        runs = self.recorded_runs()
        self.assertEqual(len(runs), 4)
        self.assertEqual(len({run["pid"] for run in runs}), 4, "each step must be a fresh process")
        for run in runs:
            self.assertEqual(run["cwd"], str(self.project))
            self.assert_prompt_argument(run["argv"])
        log = (self.loop / "loop.log").read_text().splitlines()
        self.assertEqual(len([line for line in log if re.search(r"step \d+ started", line)]), 4)
        for number in (1, 2, 3):
            self.loop_log_matches(f"step {number} outcome: progress")
        self.loop_log_matches("step 4 outcome: finished: every milestone is DONE")
        self.loop_log_matches("step 2 started: milestone M1, attempt 1")

    def test_state_not_output_decides_the_step_result(self):
        self.write_state({"M1": "TODO", "M2": "TODO"})
        outcome = self.run_to_end([{"print": "milestone DONE, all complete", "exit": 0}])
        self.assertEqual(outcome, "failed step: no state progress")
        self.assertEqual(len(self.recorded_runs()), 1)

    def test_nonzero_exit_with_state_advanced_to_all_done_is_finished(self):
        self.write_state({"M1": "TODO", "M2": "TODO"})
        outcome = self.run_to_end([{"statuses": {"M1": "DONE", "M2": "DONE"}, "exit": 1}])
        self.assertEqual(outcome, "finished: every milestone is DONE")
        self.assertEqual(len(self.recorded_runs()), 1)

    def test_milestones_file_only_change_counts_as_progress(self):
        self.write_state({"M1": "TODO"})
        plan = [{"notes": "# milestones\nM1 notes\n"}, {"statuses": {"M1": "DONE"}}]
        self.assertEqual(self.run_to_end(plan), "finished: every milestone is DONE")
        self.assertEqual(len(self.recorded_runs()), 2)

    def test_judge_step_branches(self):
        judge = load_script().judge_step

        def snap(statuses, current="M1", notes=None):
            return {"statuses": statuses, "current": current, "notes": notes}

        todo = snap({"M1": "TODO", "M2": "TODO"})
        self.assertEqual(judge(todo, todo, None, True), "stopped by owner")
        self.assertEqual(judge(todo, snap({"M1": "DONE", "M2": "DONE"}), 0, True), "stopped by owner")
        self.assertEqual(
            judge(todo, snap({"M1": "DONE", "M2": "DONE"}), 1, False), "finished: every milestone is DONE"
        )
        self.assertEqual(judge(todo, snap({"M1": "REVIEW", "M2": "TODO"}), 0, False), "progress")
        self.assertEqual(judge(todo, snap({"M1": "TODO", "M2": "TODO", "M3": "TODO"}), 0, False), "progress")
        self.assertEqual(judge(todo, snap({"M1": "TODO"}), 0, False), "progress")
        self.assertEqual(judge(todo, snap({"M1": "TODO", "M2": "TODO"}, current="M2"), 0, False), "progress")
        self.assertEqual(judge(todo, snap({"M1": "TODO", "M2": "TODO"}, notes="abc"), 0, False), "progress")
        self.assertEqual(judge(todo, snap({"M1": "REVIEW", "M2": "TODO"}), 1, False), "progress")
        self.assertEqual(judge(todo, todo, 0, False), "failed step: no state progress")
        self.assertEqual(judge(todo, todo, 1, False), "failed step: no state progress")
        empty = snap({})
        self.assertEqual(judge(empty, empty, 0, False), "failed step: no state progress")
        missing = snap(None, current=None)
        self.assertEqual(judge(missing, missing, 0, False), "failed step: no state progress")


if __name__ == "__main__":
    unittest.main()
