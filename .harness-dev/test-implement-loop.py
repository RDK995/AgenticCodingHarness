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

# Answers the sign-in check session (its prompt names the token) before recording
# anything, so the args file records step sessions only.
CHECK_PREFIX = 'case "$*" in *HARNESS_LOOP_CHECK_OK*) echo HARNESS_LOOP_CHECK_OK; exit 0;; esac\n'
SLEEPING_CLAUDE = '#!/bin/sh\n' + CHECK_PREFIX + 'echo "$@" > "{args}"\nsleep 60\n'
STUBBORN_CLAUDE = '#!/bin/sh\n' + CHECK_PREFIX + 'trap "" TERM\necho "$@" > "{args}"\nsleep 60\n'
QUICK_CLAUDE = '#!/bin/sh\n' + CHECK_PREFIX + 'echo "$@" > "{args}"\nexit 0\n'
# Records argv one per line and the environment it was given. /bin/sh itself
# adds PWD, SHLVL and _ to what it exports, so those are dropped before recording.
RECORDING_CLAUDE = (
    '#!/bin/sh\n' + CHECK_PREFIX + 'printf "%s\\n" "$@" > "{args}.tmp"\n'
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
    "Bash(git branch -m:*)",
    "Bash(git branch -M:*)",
    "Bash(git branch --move:*)",
    "Bash(git branch --force:*)",
    "Bash(git checkout -B:*)",
    "Bash(git switch -C:*)",
    "Bash(git switch --force-create:*)",
    "Bash(git reset --soft:*)",
    "Bash(git reset --mixed:*)",
    "Bash(git reset --keep:*)",
    "Bash(git reset --merge:*)",
    "Bash(git reset HEAD~*)",
    "Bash(git reset HEAD^*)",
    "Bash(git commit * --amend*)",
]
TWO = "failed steps: two in a row; last: "
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
        (self.project / ".harness" / "requirements.md").write_text("## Open Questions\n\nNone\n")
        (self.project / "README.md").write_text("fixture\n")
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "init")
        self.git("checkout", "-q", "-b", "work")
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
        self.assertEqual(outcome["outcome"], TWO + "failed step: no state progress")
        self.assertEqual(outcome["milestone"], "M2")
        self.assertIn("time", outcome)
        self.assert_prompt_argument(self.args_file.read_text().split())
        self.assertTrue(wait_for(lambda: len(self.notifications()) == 1, 2))
        self.assertEqual(len(self.notifications()), 1, self.notifications())
        self.assertTrue((self.loop / "step-1.out").exists())
        self.assertIn("step 1 outcome: failed step: no state progress", (self.loop / "loop.log").read_text())
        self.assertIn("step 2 outcome: failed step: no state progress", (self.loop / "loop.log").read_text())
        self.assertTrue((self.loop / "step-2.out").exists())

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
        self.loop_log_matches("step 2 outcome: failed step: no state progress")
        self.loop_log_matches("final outcome: " + TWO + "failed step: no state progress")

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

    def test_deny_rules_leave_path_resets_and_ordinary_commits_allowed(self):
        module = load_script()
        for rule in ("Bash(git reset:*)", "Bash(git commit:*)"):
            self.assertNotIn(rule, module.DENY_RULES)

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
            "if any('HARNESS_LOOP_CHECK_OK' in a for a in sys.argv[1:]):\n"
            "    print('HARNESS_LOOP_CHECK_OK')\n"
            "    sys.exit(0)\n"
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
        self.assertEqual(outcome, TWO + "failed step: no state progress")
        self.assertEqual(len(self.recorded_runs()), 2)

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

    # --- M4-T1: milestone cap and two-failures-in-a-row rule ---
    CAP_OUTCOME = "cap: 10 milestones reached DONE during this start"

    def test_cap_stops_after_ten_milestones_reach_done_this_start(self):
        names = [f"M{n}" for n in range(1, 13)]
        before = {"D1": "DONE", "D2": "DONE", **{name: "TODO" for name in names}}
        self.write_state(before)
        plan = [
            {"statuses": {**before, **{name: "DONE" for name in names[:count]}}, "current": names[count - 1]}
            for count in range(1, 13)
        ]
        self.assertEqual(self.run_to_end(plan), self.CAP_OUTCOME)
        self.assertEqual(len(self.recorded_runs()), 10)
        self.loop_log_matches("final outcome: " + self.CAP_OUTCOME)

    def test_split_milestone_parts_do_not_count_toward_the_cap(self):
        others = [f"M{n}" for n in range(2, 13)]
        before = {"M1": "TODO", **{name: "TODO" for name in others}}
        self.write_state(before)
        split = {"M1a": "TODO", "M1b": "TODO", **{name: "TODO" for name in others}}
        plan = [{"statuses": split}] + [
            {"statuses": {**split, **{name: "DONE" for name in others[:count]}}} for count in range(1, 12)
        ]
        self.assertEqual(self.run_to_end(plan), self.CAP_OUTCOME)
        # one split step plus ten DONE steps; counting the split would stop at 10 runs
        self.assertEqual(len(self.recorded_runs()), 11)

    def test_one_failed_step_then_progress_keeps_the_loop_running(self):
        self.write_state({"M1": "TODO", "M2": "TODO"})
        plan = [
            {},
            {"statuses": {"M1": "REVIEW", "M2": "TODO"}},
            {"statuses": {"M1": "DONE", "M2": "DONE"}},
        ]
        self.assertEqual(self.run_to_end(plan), "finished: every milestone is DONE")
        self.assertEqual(len(self.recorded_runs()), 3)
        self.loop_log_matches("step 1 outcome: failed step: no state progress")
        self.loop_log_matches("step 2 started: milestone M1, attempt 2")
        self.loop_log_matches("step 3 started: milestone M1, attempt 1")

    def test_two_failed_steps_in_a_row_stop_the_loop(self):
        self.write_state({"M1": "TODO", "M2": "TODO"})
        outcome = self.run_to_end([{}])
        self.assertEqual(outcome, "failed steps: two in a row; last: failed step: no state progress")
        self.assertEqual(len(self.recorded_runs()), 2)
        self.loop_log_matches("step 2 started: milestone M1, attempt 2")

    def test_a_crash_then_another_failure_stops_after_two_steps(self):
        self.write_state({"M1": "TODO", "M2": "TODO"})
        outcome = self.run_to_end([{"exit": 1}, {"exit": 0}])
        self.assertTrue(outcome.startswith("failed steps: two in a row"), outcome)
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


    def check_time_limit(self, body, sigkill):
        _, _, pid, step = self.start_running(body, "--step-timeout", "1", "--grace", "1")
        done = wait_for(lambda: (self.loop / "outcome.json").exists(), 15)
        self.assertTrue(done, "no outcome after the time limit")
        outcome = json.loads((self.loop / "outcome.json").read_text())
        self.assertTrue(outcome["outcome"].startswith(TWO + "failed step: time limit"), outcome)
        self.assertTrue(wait_for(lambda: not (self.loop / "driver.pid").exists(), 5))
        log_text = (self.loop / "loop.log").read_text()
        self.assertIn("step 1 exceeded time limit 1s: terminating", log_text)
        self.assertIn("SIGTERM", log_text)
        self.assertIn("step 1 outcome: failed step: time limit", log_text)
        self.assertIn("step 2 started: milestone M2, attempt 2", log_text)
        self.assertIn("step 2 outcome: failed step: time limit", log_text)
        self.assertNotIn("step 3 started", log_text)
        if sigkill:
            self.assertIn("still alive after grace: SIGKILL", log_text)
        self.assertTrue(wait_for(lambda: not group_alive(step["pid"]), 5), "step group still alive")
        self.assertFalse(alive(step["pid"]))
        self.assertEqual(len(self.notifications()), 1, self.notifications())

    def test_step_over_time_limit_is_terminated_and_recorded_as_failed(self):
        self.check_time_limit(SLEEPING_CLAUDE.replace("sleep 60", "sleep 30"), False)

    def test_step_over_time_limit_ignoring_sigterm_is_killed_after_grace(self):
        self.check_time_limit(STUBBORN_CLAUDE.replace("sleep 60", "sleep 30"), True)

    def test_timed_out_step_is_failed_even_if_state_advanced(self):
        judge = load_script().judge_step
        before = {"statuses": {"M1": "TODO"}, "current": "M1", "notes": None}
        after = {"statuses": {"M1": "REVIEW"}, "current": "M1", "notes": None}
        done = {"statuses": {"M1": "DONE"}, "current": "M1", "notes": None}
        self.assertEqual(judge(before, after, -15, False, True, 1.0), "failed step: time limit 1s exceeded")
        self.assertEqual(judge(before, done, -15, False, True, 10800.0), "failed step: time limit 10800s exceeded")

    def test_step_timeout_defaults_to_three_hours_and_is_listed_in_help(self):
        self.start(self.fake_claude(QUICK_CLAUDE))
        self.assertTrue(wait_for(lambda: (self.loop / "outcome.json").exists()))
        config = json.loads((self.loop / "config.json").read_text())
        self.assertEqual(config["step_timeout"], 10800)
        result = self.run_loop("start", "--help")
        self.assertIn("--step-timeout", result.stdout)

    def test_step_timeout_must_be_finite_and_positive(self):
        claude = self.fake_claude(QUICK_CLAUDE)
        for value in ("0", "-5", "nan", "inf", "-inf"):
            with self.subTest(value=value):
                result = self.run_loop("start", "--claude", str(claude), f"--step-timeout={value}")
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("--step-timeout", result.stderr)
                self.assertEqual(len(result.stderr.strip().splitlines()), 1, result.stderr)
                self.assertFalse((self.loop / "driver.pid").exists())
                self.assertFalse((self.loop / "config.json").exists())


    # --- M3-T1: pre-start gate ---
    def assert_refused(self, result, fragment, claude_args=None):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(fragment, result.stderr)
        self.assertFalse((self.loop / "driver.pid").exists())
        self.assertFalse((claude_args or self.args_file).exists(), "a step session started")
        lines = self.notifications()
        self.assertEqual(len(lines), 1, lines)
        self.assertIn(fragment, lines[0])

    def try_start(self, body=QUICK_CLAUDE):
        claude = self.fake_claude(body)
        return self.run_loop("start", "--claude", str(claude), "--notify-file", str(self.notify))

    def test_missing_requirements_refuse_start(self):
        (self.project / ".harness" / "requirements.md").unlink()
        self.assert_refused(self.try_start(), "requirements are missing")

    def test_open_questions_refuse_start(self):
        (self.project / ".harness" / "requirements.md").write_text("## Open Questions\n\n- Which colour?\n")
        self.assert_refused(self.try_start(), "open questions")

    def test_architecture_must_be_agreed(self):
        architecture = self.project / ".harness" / "architecture.md"
        architecture.write_text("## Status\n\nDRAFT\n")
        self.assert_refused(self.try_start(), "architecture is not agreed")
        self.notify.unlink()
        architecture.write_text("## Status\n\nAGREED\n")
        self.start(self.fake_claude(QUICK_CLAUDE))
        self.assertTrue(wait_for(lambda: (self.loop / "outcome.json").exists()))

    def test_signed_out_check_refuses_start(self):
        body = '#!/bin/sh\nif [ "$1" != "x" ]; then echo "Invalid API key · Please run /login"; exit 1; fi\n'
        result = self.try_start(body)
        self.assert_refused(result, "sign in")
        self.assertIn("exit 1", result.stderr)

    def test_check_that_cannot_see_the_skill_refuses_start(self):
        body = '#!/bin/sh\necho HARNESS_LOOP_CHECK_MISSING\nexit 0\n'
        self.assert_refused(self.try_start(body), "cannot see the harness:implement skill")

    def test_check_session_is_built_like_a_step_session(self):
        module = load_script()
        argv, env = self.run_recording_check()
        expected, _ = module.session_command(argv[0], module.CHECK_PROMPT)
        self.assertEqual(argv, expected)
        self.assertEqual(argv[argv.index("-p") + 1], module.CHECK_PROMPT)
        self.assertEqual(module.CHECK_TIMEOUT, 120)
        self.assertLessEqual(set(env), ALLOWED_ENV, sorted(set(env) - ALLOWED_ENV))
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        deny = json.loads(argv[argv.index("--settings") + 1])["permissions"]["deny"]
        for rule in REQUIRED_DENY:
            self.assertIn(rule, deny)
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "bypassPermissions")
        self.assertEqual(argv[argv.index("--permission-prompts") + 1], "none")
        self.assertEqual(Path(argv[argv.index("--plugin-dir") + 1]), ROOT)
        start = argv.index("--disallowedTools") + 1
        self.assertEqual(argv[start:start + len(deny)], deny)

    def run_recording_check(self):
        record = self.tools / "check-record"
        body = (
            '#!/bin/sh\nprintf "%s\\n" "$@" > "' + str(record) + '"\n'
            'env -u PWD -u SHLVL -u _ > "' + str(record) + '.env"\n'
            'echo HARNESS_LOOP_CHECK_OK\nexit 0\n'
        )
        path = self.tools / "claude"
        path.write_text(body)
        path.chmod(0o755)
        # argv[0] of the expected command is the resolved fake, recorded as the first element
        result = self.run_loop("check", "--claude", str(path))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        argv = [str(path)] + record.read_text().splitlines()
        env = dict(
            line.split("=", 1) for line in Path(f"{record}.env").read_text().splitlines() if "=" in line
        )
        return argv, env

    def test_check_session_over_the_limit_is_killed_and_refused(self):
        module = load_script()
        module.CHECK_TIMEOUT = 0.5
        marker = self.tools / "child.pid"
        body = f'#!/bin/sh\nsleep 30 &\necho $! > "{marker}"\nwait\n'
        path = self.tools / "claude"
        path.write_text(body)
        path.chmod(0o755)
        began = time.monotonic()
        reason = module.check_sign_in(self.project, str(path))
        self.assertLess(time.monotonic() - began, 10)
        self.assertIn("did not finish within 2 minutes", reason)
        child = int(marker.read_text().strip())
        self.pids.append(child)
        self.assertTrue(wait_for(lambda: not alive(child), 5), "check session was not killed")

    def test_protected_branches_refuse_start(self):
        self.git("checkout", "-q", "-B", "main")
        self.assert_refused(self.try_start(), "on the main branch")
        self.notify.unlink()
        self.git("checkout", "-q", "-B", "master")
        self.assert_refused(self.try_start(), "on the master branch")
        self.notify.unlink()
        self.git("checkout", "-q", "-B", "trunk")
        self.git("update-ref", "refs/remotes/origin/trunk", "HEAD")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        self.assert_refused(self.try_start(), "on the trunk branch")

    def snapshot_loop(self):
        return {
            str(path.relative_to(self.loop)): path.read_bytes()
            for path in sorted(self.loop.rglob("*")) if path.is_file()
        }

    def test_live_driver_refuses_second_start_and_is_untouched(self):
        _, _, pid, _ = self.start_running(SLEEPING_CLAUDE)
        before = self.snapshot_loop()
        result = self.run_loop("start", "--claude", str(self.tools / "claude"), "--notify-file", str(self.notify))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"pid {pid}", result.stderr)
        self.assertEqual(len(self.notifications()), 1, self.notifications())
        self.assertIn("loop did not start", self.notifications()[0])
        self.assertTrue(alive(pid))
        self.assertEqual(self.snapshot_loop(), before)

    def test_check_subcommand_reports_without_starting(self):
        claude = self.fake_claude(QUICK_CLAUDE)
        result = self.run_loop("check", "--claude", str(claude))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("check passed", result.stdout)
        self.assertIn("-p <prompt: ", result.stdout)
        self.assertNotIn("harness:implement is available", result.stdout)
        self.assertFalse((self.project / ".harness" / "loop").exists())
        self.assertEqual(self.notifications(), [])

        missing = self.fake_claude('#!/bin/sh\necho HARNESS_LOOP_CHECK_MISSING\n')
        result = self.run_loop("check", "--claude", str(missing))
        self.assertEqual(result.returncode, 1)
        self.assertIn("check failed", result.stdout)
        self.assertFalse((self.project / ".harness" / "loop").exists())
        self.assertEqual(self.notifications(), [])


if __name__ == "__main__":
    unittest.main()
