#!/usr/bin/env python3
"""Start, report on, and stop the unattended implement loop's background driver.

`start` launches a detached driver process (its own session, not a child of the
caller) and returns. The driver keeps the Mac awake with `caffeinate -w <pid>`,
runs successive fresh `/harness:implement` steps, decides after each in `judge_step`
from the recorded state,
and ends with exactly one stop notification. `status` and `stop` find the driver
through `.harness/loop/driver.pid`.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True

SCRIPT = Path(__file__).resolve()
HARNESS_ROOT = SCRIPT.parent.parent
STEP_PROMPT = "/harness:implement"
DEFAULT_GRACE = 20.0
DEFAULT_STEP_TIMEOUT = 3 * 60 * 60
START_WAIT = 4.0
STOP_EXTRA_WAIT = 10.0
POLL = 0.1
CHECK_TIMEOUT = 120  # seconds the sign-in check session may run (2 minutes)
CHECK_OK = "HARNESS_LOOP_CHECK_OK"
CHECK_MISSING = "HARNESS_LOOP_CHECK_MISSING"
CHECK_PROMPT = (
    "If a skill named harness:implement is available to you, reply with exactly "
    f"{CHECK_OK}; otherwise reply with exactly {CHECK_MISSING}. Use no tools."
)

RESULT_MARKER = "HARNESS_LOOP_RESULT:"
RESULT_INSTRUCTION = (
    "When you finish, end your final message with exactly one line: "
    f"`{RESULT_MARKER} BOUNDARY` if you stopped at a normal milestone or phase boundary "
    "(for example a milestone set to REVIEW, DONE or SPLIT, or a phase handed off), or "
    f"`{RESULT_MARKER} HUMAN \u2014 <one plain sentence saying what the owner must decide or do>` "
    "if you stopped for the human for any other reason (a milestone BLOCKED, an escalation, "
    "a decision needed, an exhausted continuation, retry or review-cycle cap, a planning stop, "
    "or anything else)."
)
SIGNED_OUT_PHRASES = (
    "not logged in", "please run /login", "invalid api key", "oauth token has expired", "authentication_error",
)
USAGE_LIMIT_PHRASES = ("usage limit", "hit your limit", "limit reached")

# The only parent environment names a session may see. Each passes through only
# when set in the parent; GIT_TERMINAL_PROMPT is always forced to "0".
SESSION_ENV_NAMES = (
    "PATH",
    "HOME",
    "USER",
    "GIT_TERMINAL_PROMPT",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "CLAUDE_CONFIG_DIR",
)

# Commands an unattended session must never run, in Claude Code permission-rule
# syntax. Passed both as --disallowedTools values and as --settings
# permissions.deny. Committing on the milestone branch stays allowed, so a commit
# on main is blocked by denying every way of moving onto main (checkout, switch,
# forced create-and-switch, forced branch moves and renames, ref rewrites); M3's
# start gate also refuses to run on main. History rewrites are denied too: every
# non-path reset (--soft, --mixed, --keep, --merge, HEAD~/HEAD^) and an amend
# wherever --amend appears on the line. A plain `git reset <path>` and ordinary
# commits stay allowed. "<prefix>:*" matches the prefix followed by a space or the
# end of the line; a bare "*" is a wildcard for any text, so HEAD~ and HEAD^ (whose
# count follows with no space) and the mid-line amend use "*".
DENY_RULES = (
    "Bash(git push:*)",
    "Bash(git merge:*)",
    "Bash(git pull:*)",
    "Bash(gh pr merge:*)",
    "Bash(git rebase:*)",
    "Bash(git reset --hard:*)",
    "Bash(git commit --amend:*)",
    "Bash(git filter-branch:*)",
    "Bash(git filter-repo:*)",
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
)


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def state_dir(project: Path) -> Path:
    return project / ".harness" / "loop"


def write_atomic(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text)
    os.replace(temporary, path)


def write_json(path: Path, value: dict) -> None:
    write_atomic(path, json.dumps(value, indent=2) + "\n")


def read_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def log(project: Path, message: str) -> None:
    """The single loop.log writer: one timestamped human-readable line per event."""
    with open(state_dir(project) / "loop.log", "a") as handle:
        handle.write(f"{now()} {message}\n")


def record_command(project: Path, pid: int, command: list[str]) -> None:
    """The single commands.log writer: one timestamped line per child process started."""
    with open(state_dir(project) / "commands.log", "a") as handle:
        handle.write(f"{now()} pid {pid}: {describe_command(command)}\n")


def describe_command(command: list[str]) -> str:
    """Render a child command line for the log, showing a prompt by length only."""
    shown = []
    for index, part in enumerate(command):
        if index > 0 and command[index - 1] == "-p":
            shown.append(f"<prompt: {len(part)} chars>")
        else:
            shown.append(part)
    return " ".join(shown)


def session_command(claude: str, prompt: str, parent_env=None) -> tuple[list[str], dict[str, str]]:
    """Return the locked-down command line and minimal environment for one claude session."""
    parent = os.environ if parent_env is None else parent_env
    rules = list(DENY_RULES)
    command = [
        claude,
        "--permission-mode",
        "bypassPermissions",
        "--permission-prompts",
        "none",
        "--plugin-dir",
        str(HARNESS_ROOT),
        "--settings",
        json.dumps({"permissions": {"deny": rules}}),
        "--disallowedTools",
        *rules,
        "--append-system-prompt",
        RESULT_INSTRUCTION,
        "-p",
        prompt,
    ]
    env = {name: parent[name] for name in SESSION_ENV_NAMES if name in parent}
    env["GIT_TERMINAL_PROMPT"] = "0"
    return command, env


def current_milestone(project: Path) -> str | None:
    state = read_json(project / ".harness" / "state.json")
    milestones = state.get("milestones") if state else None
    if not isinstance(milestones, dict):
        return None
    for identifier, milestone in milestones.items():
        if not isinstance(milestone, dict) or milestone.get("status") != "DONE":
            return identifier
    return None


# Notification seam: `notify` picks a sink from the persisted config.
def file_sink(path: str):
    def send(message: str) -> str:
        with open(path, "a") as handle:
            handle.write(f"{now()} {message}\n")
        return f"file {path}"

    return send


def choose_sink(config: dict):
    if config.get("notify_file"):
        return file_sink(config["notify_file"])
    return None


def notify(project: Path, config: dict, message: str) -> None:
    sink = choose_sink(config)
    if sink is None:
        log(project, f"notification not sent: no sink configured: {message}")
        return
    try:
        where = sink(message)
    except OSError as error:
        log(project, f"notification not sent: {error}: {message}")
        return
    log(project, f"notification sent ({where}): {message}")


# Driver identity and liveness.
def read_pid(project: Path) -> int | None:
    try:
        return int((state_dir(project) / "driver.pid").read_text().strip())
    except (OSError, ValueError):
        return None


def is_driver(pid: int) -> bool:
    """True only for a live process that is this script's driver (a recycled pid is stale)."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return False
    command = subprocess.run(
        ["ps", "-o", "command=", "-p", str(pid)], text=True, capture_output=True, check=False
    ).stdout
    return "implement-loop" in command and " _driver" in command


def process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def group_exists(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def running_driver(project: Path) -> int | None:
    """Return the live driver's pid, removing a stale pid file."""
    pid = read_pid(project)
    pid_file = state_dir(project) / "driver.pid"
    if pid is not None and is_driver(pid):
        return pid
    if pid_file.exists():
        pid_file.unlink(missing_ok=True)
    return None


# The driver.
PROGRESS = "progress"
FINISHED = "finished: every milestone is DONE"
FAILED_STEP = "failed step: no state progress"
MILESTONE_CAP = 10
CAP_REACHED = f"cap: {MILESTONE_CAP} milestones reached DONE during this start"


def done_milestones(project: Path) -> set[str]:
    """Ids of the milestones whose status is DONE in state.json (empty without state)."""
    snapshot = take_snapshot(project)["statuses"] or {}
    return {identifier for identifier, status in snapshot.items() if status == "DONE"}


def take_snapshot(project: Path) -> dict:
    """Record what the judge compares: milestone statuses, current milestone, milestones.md hash."""
    state = read_json(project / ".harness" / "state.json")
    milestones = state.get("milestones") if state else None
    statuses = None
    if isinstance(milestones, dict):
        statuses = {
            identifier: milestone.get("status") if isinstance(milestone, dict) else None
            for identifier, milestone in milestones.items()
        }
    try:
        notes = hashlib.sha256((project / ".harness" / "milestones.md").read_bytes()).hexdigest()
    except OSError:
        notes = None
    return {
        "statuses": statuses,
        "current": state.get("current_milestone") if state else None,
        "notes": notes,
    }


def reset_time(output: str) -> str | None:
    """The usage-limit reset time the output gives (text after resets / reset at, or a |epoch suffix)."""
    found = re.search(r"resets?(?: at)?[ \t]+([^\n\u00b7|]*)", output, re.IGNORECASE)
    if found and found.group(1).strip():
        return found.group(1).strip()
    epoch = re.search(r"\|\s*(\d{9,11})\b", output)
    if epoch:
        return datetime.fromtimestamp(int(epoch.group(1))).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    return None


def account_stop(output: str) -> str | None:
    """Return the outcome when the output says Claude is signed out or the usage limit is reached."""
    lowered = output.lower()
    if any(phrase in lowered for phrase in SIGNED_OUT_PHRASES):
        return "signed out of Claude"
    if any(phrase in lowered for phrase in USAGE_LIMIT_PHRASES):
        reset = reset_time(output)
        return "usage limit reached" + (f" (resets {reset})" if reset else "")
    return None


def human_stop(before: dict, after: dict, output: str) -> str | None:
    """Return the outcome when the session stopped for the human, from state first, then its result line."""
    for identifier, status in (after["statuses"] or {}).items():
        if status == "BLOCKED":
            return f"stopped for the human: milestone {identifier} is BLOCKED"
    if before["notes"] is None and after["notes"] is not None:
        return "stopped for the human: milestones planned; review the plan"
    results = [line.strip() for line in output.splitlines() if line.strip().startswith(RESULT_MARKER)]
    if results:
        verdict = results[-1][len(RESULT_MARKER):].strip()
        if verdict.upper().startswith("HUMAN"):
            sentence = verdict[len("HUMAN"):].lstrip(" \t\u2014-\u2013:").strip()
            return f"stopped for the human: {sentence}" if sentence else "stopped for the human"
    return None


def judge_step(before: dict, after: dict, returncode: int | None, stopped: bool,
               timed_out: bool = False, step_timeout: float = DEFAULT_STEP_TIMEOUT,
               output: str = "") -> str:
    """Decide what follows a step from recorded state; the exit code never decides progress."""
    if stopped:
        return "stopped by owner"
    account = account_stop(output)
    if account:
        return account
    if timed_out:  # a step that overran its limit failed, whatever state it changed
        return f"failed step: time limit {step_timeout:g}s exceeded"
    statuses = after["statuses"]
    if statuses and all(status == "DONE" for status in statuses.values()):
        return FINISHED
    human = human_stop(before, after, output)
    if human:
        return human
    if before != after:
        return PROGRESS
    return FAILED_STEP


class Driver:
    def __init__(self, project: Path):
        self.project = project
        self.loop = state_dir(project)
        self.config = read_json(self.loop / "config.json") or {}
        self.grace = float(self.config.get("grace", DEFAULT_GRACE))
        self.step_timeout = float(self.config.get("step_timeout", DEFAULT_STEP_TIMEOUT))
        self.stop_requested = False
        self.finished = False
        self.notified = False
        self.caffeinate: subprocess.Popen | None = None
        self.step: subprocess.Popen | None = None
        self.milestone: str | None = None
        self.output = ""

    def request_stop(self, signum, _frame) -> None:
        self.stop_requested = True

    def spawn(self, command: list[str], **options) -> subprocess.Popen:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, close_fds=True, **options)
        log(self.project, f"child started pid {process.pid}: {describe_command(command)}")
        record_command(self.project, process.pid, command)
        return process

    def start_caffeinate(self) -> None:
        binary = os.environ.get("HARNESS_LOOP_CAFFEINATE", "caffeinate")
        try:
            self.caffeinate = self.spawn(
                [binary, "-w", str(os.getpid())],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as error:
            log(self.project, f"caffeinate not started: {error}")

    def stop_caffeinate(self) -> None:
        if self.caffeinate is None or self.caffeinate.poll() is not None:
            return
        self.caffeinate.terminate()
        try:
            self.caffeinate.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.caffeinate.kill()
            self.caffeinate.wait()

    def terminate_step(self) -> None:
        """SIGTERM the step's process group, then SIGKILL it if still alive after the grace period."""
        step = self.step
        if step is None:
            return
        pgid = step.pid
        log(self.project, f"stopping step group {pgid}: SIGTERM, grace {self.grace:g}s")
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + self.grace
        while time.monotonic() < deadline:
            step.poll()
            if not group_exists(pgid):
                break
            time.sleep(POLL)
        else:
            log(self.project, f"step group {pgid} still alive after grace: SIGKILL")
            try:
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        step.wait()

    def run_step(self, number: int, attempt: int) -> tuple[int | None, bool, bool]:
        self.milestone = current_milestone(self.project)
        claude = self.config.get("claude") or "claude"
        command, env = session_command(claude, STEP_PROMPT)
        log(self.project, f"step {number} started: milestone {self.milestone}, attempt {attempt}")
        out_path = self.loop / f"step-{number}.out"
        offset = out_path.stat().st_size if out_path.exists() else 0  # an earlier start may have used this name
        with open(out_path, "ab") as output:
            self.step = self.spawn(
                command,
                cwd=self.project,
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        deadline = time.monotonic() + self.step_timeout
        timed_out = False
        write_json(
            self.loop / "current-step.json",
            {
                "step": number,
                "milestone": self.milestone,
                "attempt": attempt,
                "pid": self.step.pid,
                "started": now(),
            },
        )
        while self.step.poll() is None:
            if self.stop_requested:
                self.terminate_step()
                break
            if time.monotonic() >= deadline:
                timed_out = True
                log(self.project, f"step {number} exceeded time limit {self.step_timeout:g}s: terminating")
                self.terminate_step()
                break
            time.sleep(POLL)
        returncode = self.step.returncode
        log(self.project, f"step {number} ended: exit {returncode}")
        with open(out_path, "rb") as handle:
            handle.seek(offset)
            self.output = handle.read().decode("utf-8", errors="replace")
        return returncode, self.stop_requested, timed_out

    def finish(self, outcome: str) -> None:
        if self.finished:
            return
        self.finished = True
        if self.step is not None and self.step.poll() is None:
            self.terminate_step()
        self.stop_caffeinate()
        write_json(
            self.loop / "outcome.json",
            {"outcome": outcome, "time": now(), "milestone": self.milestone},
        )
        log(self.project, f"final outcome: {outcome}")
        if not self.notified:
            self.notified = True
            notify(
                self.project,
                self.config,
                f"implement loop stopped: {outcome} (milestone {self.milestone})",
            )
        pid_file = self.loop / "driver.pid"
        if read_pid(self.project) == os.getpid():
            pid_file.unlink(missing_ok=True)

    def run(self) -> int:
        for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(signum, self.request_stop)
        write_atomic(self.loop / "driver.pid", f"{os.getpid()}\n")
        log(self.project, f"driver started: pid {os.getpid()}, project {self.project}")
        outcome = "driver error"
        try:
            self.start_caffeinate()
            done_before = done_milestones(self.project)
            failures = 0
            for number in itertools.count(1):
                if self.stop_requested:
                    outcome = "stopped by owner"
                    break
                before = take_snapshot(self.project)
                returncode, stopped, timed_out = self.run_step(number, failures + 1)
                outcome = judge_step(
                    before, take_snapshot(self.project), returncode, stopped, timed_out, self.step_timeout,
                    self.output,
                )
                log(self.project, f"step {number} outcome: {outcome}")
                if outcome == PROGRESS:
                    failures = 0
                    if len(done_milestones(self.project) - done_before) >= MILESTONE_CAP:
                        outcome = CAP_REACHED
                        break
                elif outcome.startswith("failed step"):
                    failures += 1
                    if failures >= 2:
                        outcome = f"failed steps: two in a row; last: {outcome}"
                        break
                else:
                    break
        except Exception as error:  # the driver must always end with its notification
            outcome = f"driver error: {error}"
            log(self.project, outcome)
        finally:
            self.finish(outcome)
        return 0


# Commands.
def resolve_claude(option: str | None) -> str | None:
    candidate = option or os.environ.get("HARNESS_LOOP_CLAUDE") or "claude"
    if os.sep in candidate:
        path = Path(candidate).expanduser().resolve()
        return str(path) if os.access(path, os.X_OK) else None
    return shutil.which(candidate)


def section_body(text: str, heading: str) -> str | None:
    """Return the stripped text under `## <heading>` up to the next `## ` heading, or None."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            body = []
            for following in lines[index + 1:]:
                if following.startswith("## "):
                    break
                body.append(following)
            return "\n".join(body).strip()
    return None


def check_documents(project: Path) -> str | None:
    requirements = project / ".harness" / "requirements.md"
    try:
        text = requirements.read_text()
    except OSError:
        return "requirements are missing; write them (roast-requirements) before starting"
    if section_body(text, "Open Questions") != "None":
        return "requirements have open questions; answer them (roast-requirements) before starting"
    architecture = project / ".harness" / "architecture.md"
    if architecture.exists():
        status = section_body(architecture.read_text(), "Status")
        first = status.splitlines()[0].strip() if status else ""
        if first != "AGREED":
            return "the architecture is not agreed; agree it before starting"
    return None


def git_output(project: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(project), *args], text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def check_branch(project: Path) -> str | None:
    branch = git_output(project, "rev-parse", "--abbrev-ref", "HEAD")
    if branch is None:  # not a git repository: implement handles that
        return None
    protected = {"main", "master"}
    default = git_output(project, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    if default:
        protected.add(default.removeprefix("origin/"))
    if branch in protected:
        return f"on the {branch} branch; switch to a working branch first"
    return None


def check_sign_in(project: Path, claude: str) -> str | None:
    command, env = session_command(claude, CHECK_PROMPT)
    try:
        process = subprocess.Popen(
            command,
            cwd=project,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            close_fds=True,
            start_new_session=True,
        )
    except OSError as error:
        return f"Claude did not start the sign-in check: {error}"
    try:
        stdout, stderr = process.communicate(timeout=CHECK_TIMEOUT)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        return "the sign-in check did not finish within 2 minutes"
    if process.returncode != 0:
        lines = [line.strip() for line in (stdout + "\n" + stderr).splitlines() if line.strip()]
        first = lines[0][:200] if lines else ""
        return (
            f"Claude did not answer the sign-in check (exit {process.returncode}): {first}; "
            "sign in to Claude and try again"
        )
    if CHECK_OK not in stdout or CHECK_MISSING in stdout:
        return "Claude cannot see the harness:implement skill; check the harness plugin is installed"
    return None


def pre_start_gate(project: Path, claude: str) -> str | None:
    """Run the pre-start checks in order and return the first failure reason, or None."""
    pid = running_driver(project)
    if pid is not None:
        return f"a driver is already running (pid {pid}); run stop first, or wait for it to finish"
    return check_documents(project) or check_branch(project) or check_sign_in(project, claude)


def refuse(reason: str, notify_file: str | None) -> int:
    """Refuse to start: say why on stderr, send one notification, write nothing under .harness/loop."""
    print(f"cannot start: {reason}", file=sys.stderr)
    sink = choose_sink({"notify_file": notify_file})
    if sink is None:
        print("notification not sent: no sink configured", file=sys.stderr)
    else:
        try:
            sink(f"loop did not start: {reason}")
        except OSError as error:
            print(f"notification not sent: {error}", file=sys.stderr)
    return 1


def command_start(args, project: Path) -> int:
    if not (math.isfinite(args.step_timeout) and args.step_timeout > 0):
        print("cannot start: --step-timeout must be a positive number of seconds", file=sys.stderr)
        return 2
    claude = resolve_claude(args.claude)
    if claude is None:
        print("cannot start: claude executable not found", file=sys.stderr)
        return 2
    notify_file = str(Path(args.notify_file).expanduser().resolve()) if args.notify_file else None
    reason = pre_start_gate(project, claude)
    if reason is not None:
        return refuse(reason, notify_file)
    loop = state_dir(project)
    loop.mkdir(parents=True, exist_ok=True)
    (loop / ".gitignore").write_text("*\n")
    write_json(
        loop / "config.json",
        {"claude": claude, "notify_file": notify_file, "grace": args.grace, "step_timeout": args.step_timeout},
    )
    for stale in ("current-step.json", "outcome.json"):
        (loop / stale).unlink(missing_ok=True)

    driver = subprocess.Popen(
        [sys.executable, str(SCRIPT), "_driver", "--project", str(project)],
        cwd=project,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=True,
    )
    deadline = time.monotonic() + START_WAIT
    while time.monotonic() < deadline:
        if read_pid(project) == driver.pid or driver.poll() is not None:
            break
        time.sleep(0.05)
    if read_pid(project) == driver.pid or (loop / "outcome.json").exists():
        print(f"started (pid {driver.pid})")
        return 0
    print(f"driver (pid {driver.pid}) did not record its pid; see {loop / 'loop.log'}", file=sys.stderr)
    return 1


def command_check(args, project: Path) -> int:
    claude = resolve_claude(args.claude)
    if claude is None:
        print("cannot check: claude executable not found", file=sys.stderr)
        return 2
    command, _ = session_command(claude, CHECK_PROMPT)
    print(describe_command(command))
    reason = pre_start_gate(project, claude)
    if reason is not None:
        print(f"check failed: {reason}")
        return 1
    print("check passed: harness:implement is visible")
    return 0


def command_status(args, project: Path) -> int:
    pid = running_driver(project)
    if pid is None:
        print("not running")
        return 0
    step = read_json(state_dir(project) / "current-step.json") or {}
    print("running")
    print(f"pid: {pid}")
    print(f"step: {step.get('step', 'not started')}")
    print(f"milestone: {step.get('milestone') if step else current_milestone(project)}")
    return 0


def command_stop(args, project: Path) -> int:
    pid = running_driver(project)
    if pid is None:
        print("not running")
        return 0
    config = read_json(state_dir(project) / "config.json") or {}
    limit = float(config.get("grace", DEFAULT_GRACE)) + STOP_EXTRA_WAIT
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        if not process_exists(pid):
            print(f"stopped (pid {pid})")
            return 0
        time.sleep(POLL)
    print(f"driver (pid {pid}) did not exit within {limit:g}s", file=sys.stderr)
    return 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start", help="launch the background driver")
    start.add_argument("--claude", help="claude executable (default: $HARNESS_LOOP_CLAUDE or claude on PATH)")
    start.add_argument("--notify-file", help="append notifications to this file")
    start.add_argument("--grace", type=float, default=DEFAULT_GRACE, help="seconds between SIGTERM and SIGKILL")
    start.add_argument(
        "--step-timeout", type=float, default=DEFAULT_STEP_TIMEOUT, help="seconds a step may run (default: 10800)"
    )
    check = commands.add_parser("check", help="run the pre-start checks without starting")
    check.add_argument("--claude", help="claude executable (default: $HARNESS_LOOP_CLAUDE or claude on PATH)")
    commands.add_parser("status", help="report whether the driver is running")
    commands.add_parser("stop", help="stop the driver and its current step")
    commands.add_parser("_driver", help=argparse.SUPPRESS)
    for sub in commands.choices.values():
        sub.add_argument("--project", default=".", help="project directory (default: current directory)")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    project = Path(args.project).expanduser().resolve()
    if args.command == "_driver":
        return Driver(project).run()
    return {"start": command_start, "check": command_check, "status": command_status, "stop": command_stop}[args.command](args, project)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
