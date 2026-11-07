#!/usr/bin/env python3
"""Start, report on, and stop the unattended implement loop's background driver.

`start` launches a detached driver process (its own session, not a child of the
caller) and returns. The driver keeps the Mac awake with `caffeinate -w <pid>`,
runs one `/harness:implement` step, decides what happens next in `judge_step`,
and ends with exactly one stop notification. `status` and `stop` find the driver
through `.harness/loop/driver.pid`.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True

SCRIPT = Path(__file__).resolve()
STEP_PROMPT = "/harness:implement"
DEFAULT_GRACE = 20.0
START_WAIT = 4.0
STOP_EXTRA_WAIT = 10.0
POLL = 0.1


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
def judge_step(returncode: int | None, stopped: bool) -> str:
    """Decide what follows a step. M1: one step, then the driver ends."""
    if stopped:
        return "stopped by owner"
    return "finished one step"


class Driver:
    def __init__(self, project: Path):
        self.project = project
        self.loop = state_dir(project)
        self.config = read_json(self.loop / "config.json") or {}
        self.grace = float(self.config.get("grace", DEFAULT_GRACE))
        self.stop_requested = False
        self.finished = False
        self.notified = False
        self.caffeinate: subprocess.Popen | None = None
        self.step: subprocess.Popen | None = None
        self.milestone: str | None = None

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

    def run_step(self, number: int, attempt: int) -> tuple[int | None, bool]:
        self.milestone = current_milestone(self.project)
        claude = self.config.get("claude") or "claude"
        command = [claude, "-p", STEP_PROMPT]
        log(self.project, f"step {number} started: milestone {self.milestone}, attempt {attempt}")
        with open(self.loop / f"step-{number}.out", "ab") as output:
            self.step = self.spawn(
                command,
                cwd=self.project,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
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
            time.sleep(POLL)
        returncode = self.step.returncode
        log(self.project, f"step {number} ended: exit {returncode}")
        return returncode, self.stop_requested

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
            if self.stop_requested:
                outcome = judge_step(None, True)
            else:
                returncode, stopped = self.run_step(1, 1)
                outcome = judge_step(returncode, stopped)
                log(self.project, f"step 1 outcome: {outcome}")
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


def command_start(args, project: Path) -> int:
    loop = state_dir(project)
    loop.mkdir(parents=True, exist_ok=True)
    (loop / ".gitignore").write_text("*\n")
    pid = running_driver(project)
    if pid is not None:
        print(f"already running (pid {pid})")
        return 1
    claude = resolve_claude(args.claude)
    if claude is None:
        print("cannot start: claude executable not found", file=sys.stderr)
        return 2
    notify_file = str(Path(args.notify_file).expanduser().resolve()) if args.notify_file else None
    write_json(loop / "config.json", {"claude": claude, "notify_file": notify_file, "grace": args.grace})
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
    return {"start": command_start, "status": command_status, "stop": command_stop}[args.command](args, project)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
