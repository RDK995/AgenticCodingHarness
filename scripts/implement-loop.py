#!/usr/bin/env python3
"""Run /harness:implement repeatedly, each time in a brand-new session.

A fresh session is the `/clear` the implement skill asks the human for at every
milestone boundary. Each one is an ordinary background session (`claude --bg`):
`claude attach <id>` shows it exactly as an interactive session looks, and a
permission prompt waits there for the human to answer. Whether to run again is
decided from repository state alone -- `.harness/state.json` and
`git rev-parse HEAD` -- never from what the session said.

When every milestone is DONE the loop runs one more session -- the one in
which implement runs its all-DONE gate and writes the final report -- then runs
that gate itself, and succeeds only if it passes. One loop runs per checkout at
a time: a second exits at once.

Run from the project root. Exit status:
  0  every milestone is DONE and the all-DONE gate passes
  3  stopped by a condition: a BLOCKED milestone, a status the implement skill
     has no branch for, no progress, --until reached, or --max reached
  1  error: a session could not start or ended without finishing, state could
     not be read, the all-DONE gate failed, or another loop holds this checkout
  2  bad usage
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True

EXIT_ALL_DONE = 0
EXIT_ERROR = 1
EXIT_STOPPED = 3

# Statuses the implement skill's LOOP acts on for the selected milestone.
# Anything else (e.g. DEFERRED) has no branch there, so running it would spend
# an iteration to learn nothing.
RUNNABLE = {"TODO", "IN_PROGRESS", "REVIEW"}
PERMISSION_MODES = ("acceptEdits", "auto", "bypassPermissions", "manual", "dontAsk", "plan")
DEFAULT_PERMISSION_MODE = "acceptEdits"
DEFAULT_MAX = 10
STATE = Path(".harness/state.json")
MILESTONES = Path(".harness/milestones.md")
REQUIREMENTS = Path(".harness/requirements.md")
CHECK_STATE = Path(__file__).resolve().parent / "check-state.py"
LOG_DIR = Path(".harness/evidence/implement-loop")
POLL_SECONDS = float(os.environ.get("HARNESS_LOOP_POLL_SECONDS", "5"))
# How long a launched session may take to appear in `claude agents`.
APPEAR_SECONDS = 60


class StateError(Exception):
    pass


def read_state(root: Path) -> tuple[dict, str]:
    path = root / STATE
    try:
        raw = path.read_bytes()
        state = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        raise StateError(f"cannot read {STATE}: {error}") from error
    milestones = state.get("milestones") if isinstance(state, dict) else None
    if not isinstance(milestones, dict):
        raise StateError(f"{STATE} has no milestones object")
    return state, hashlib.sha256(raw).hexdigest()


def select(state: dict) -> tuple[str, str] | None:
    """Mirror the implement skill: the first milestone, in order, that is not DONE."""
    for milestone_id, milestone in state["milestones"].items():
        status = milestone.get("status") if isinstance(milestone, dict) else None
        if status != "DONE":
            return milestone_id, str(status)
    return None


def status_of(state: dict, milestone_id: str) -> str:
    milestone = state["milestones"].get(milestone_id)
    if not isinstance(milestone, dict):
        return "absent"
    return str(milestone.get("status"))


def head(root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def short(sha: str | None) -> str:
    return sha[:7] if sha else "no-git"


def ignore_log_dir(root: Path) -> None:
    # The launcher skill writes this loop's output here. Keep it out of git: an
    # untracked file would otherwise be swept into the next milestone branch's
    # first commit by the implement skill.
    directory = root / LOG_DIR
    directory.mkdir(parents=True, exist_ok=True)
    ignore = directory / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n")


# Background sessions may not edit the main checkout by default; they are meant
# to work in a worktree of their own. Implement has to work in place: its state
# file and milestone branches live in this checkout, and the loop reads them here.
IN_PLACE = json.dumps({"worktree": {"bgIsolation": "none"}})


def command(args: argparse.Namespace, name: str) -> list[str]:
    argv = ["claude", "--bg", "--name", name, "--settings", IN_PLACE, "--permission-mode", args.permission_mode]
    if args.plugin_dir:
        argv += ["--plugin-dir", str(args.plugin_dir)]
    return argv + ["/harness:implement"]


class SessionError(Exception):
    pass


def find_session(name: str) -> dict | None:
    completed = subprocess.run(
        ["claude", "agents", "--json", "--all"], text=True, capture_output=True, check=False
    )
    if completed.returncode != 0:
        return None
    try:
        sessions = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None
    matches = [s for s in sessions if isinstance(s, dict) and s.get("name") == name]
    return max(matches, key=lambda s: s.get("startedAt", 0)) if matches else None


def wait_for(name: str, label: str) -> str:
    """Block until the session called `name` finishes its turn; return its id.

    Reports, once each time it changes, what the session is waiting on, so the
    human knows to attach and answer it.
    """
    deadline = time.monotonic() + APPEAR_SECONDS
    session = find_session(name)
    while session is None or "id" not in session:
        if time.monotonic() > deadline:
            raise SessionError(f"session {name!r} never appeared in `claude agents`")
        time.sleep(POLL_SECONDS)
        session = find_session(name)
    session_id = session["id"]
    print(f"{label} started -- watch it: claude attach {session_id}", flush=True)
    reported = None
    while True:
        state = session.get("state")
        if state == "done":
            return session_id
        if state == "stopped":
            raise SessionError(f"session {session_id} was stopped before it finished")
        # "blocked" is a turn paused on the human: a permission prompt (which
        # names itself in waitingFor) or anything else that needs their input.
        waiting = (session.get("waitingFor") or "your input") if state == "blocked" else None
        if waiting != reported:
            if waiting:
                print(f"{label} is waiting for you ({waiting}) -- claude attach {session_id}", flush=True)
            reported = waiting
        time.sleep(POLL_SECONDS)
        session = find_session(name)
        if session is None:
            raise SessionError(f"session {session_id} disappeared before it finished")


def stop(reason: str, code: int) -> int:
    print(f"STOP: {reason}", flush=True)
    return code


def lock(root: Path):
    """Hold this checkout for one loop: (open lock file, None), or (None, owner pid).

    Two loops would run in-place sessions on the same milestone, branching and
    committing in one working tree. The lock goes with the process, however it
    ends.
    """
    handle = (root / LOG_DIR / ".lock").open("a+")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.seek(0)
        owner = handle.read().strip() or "unknown"
        handle.close()
        return None, owner
    handle.seek(0)
    handle.truncate()
    handle.write(f"{os.getpid()}\n")
    handle.flush()
    return handle, None


def all_done_gate(root: Path) -> list[str]:
    completed = subprocess.run(
        [
            sys.executable,
            str(CHECK_STATE),
            str(root / STATE),
            "--milestones",
            str(root / MILESTONES),
            "--requirements",
            str(root / REQUIREMENTS),
            "--all-done",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0:
        return []
    return [line.removeprefix("ERROR: ") for line in completed.stderr.splitlines() if line.strip()] or [
        f"check-state.py exited with status {completed.returncode}"
    ]


def run_session(args: argparse.Namespace, root: Path, name: str, label: str) -> str:
    """Start one /harness:implement session, wait for its turn to end, close it."""
    try:
        launched = subprocess.run(
            command(args, name), cwd=root, stdin=subprocess.DEVNULL, text=True, capture_output=True, check=False
        )
    except OSError as error:
        raise SessionError(f"could not start claude: {error}") from error
    if launched.returncode != 0:
        raise SessionError(
            f"claude --bg exited with status {launched.returncode}: {(launched.stdout + launched.stderr).strip()}"
        )
    session_id = wait_for(name, label)
    # The turn is over. Stopping keeps the conversation: `claude attach`
    # reopens it, and it stays listed under `claude agents --all`.
    subprocess.run(["claude", "stop", session_id], capture_output=True, check=False)
    return session_id


def run(args: argparse.Namespace) -> int:
    root = Path.cwd()
    ignore_log_dir(root)
    held, owner = lock(root)
    if held is None:
        return stop(f"another implement-loop (pid {owner}) is already running in this checkout", EXIT_ERROR)
    try:
        state, digest = read_state(root)
    except StateError as error:
        return stop(str(error), EXIT_ERROR)

    if args.until is not None:
        if args.until not in state["milestones"]:
            return stop(f"--until {args.until} is not a milestone in {STATE}", EXIT_ERROR)
        if status_of(state, args.until) == "DONE":
            return stop(f"--until {args.until} is already DONE", EXIT_ERROR)

    iteration = 0
    reported = False
    while True:
        selected = select(state)
        if selected is None and reported:
            errors = all_done_gate(root)
            if errors:
                return stop("every milestone is DONE but the all-DONE check failed: " + "; ".join(errors), EXIT_ERROR)
            return stop("all milestones are DONE and the all-DONE check passed", EXIT_ALL_DONE)
        if selected is None:
            # Implement runs its all-DONE gate and writes the final report only
            # in a fresh session that finds nothing left; the session that
            # finished the last milestone stopped at its boundary. This one is
            # not counted against --max, and it is expected to change nothing.
            reported = True
            iteration += 1
            name = f"implement-loop final #{iteration} {datetime.now(timezone.utc):%Y%m%dT%H%M%SZ} {os.getpid()}"
            try:
                session_id = run_session(args, root, name, f"[{iteration}] final report")
                state, digest = read_state(root)
            except (SessionError, StateError) as error:
                return stop(str(error), EXIT_ERROR)
            print(f"[{iteration}] final report written (session {session_id})", flush=True)
            continue
        milestone_id, status = selected
        if status == "BLOCKED":
            return stop(f"{milestone_id} is BLOCKED and needs a human decision", EXIT_STOPPED)
        if status not in RUNNABLE:
            return stop(
                f"{milestone_id} has status {status}, which /harness:implement has no step for",
                EXIT_STOPPED,
            )
        if args.until == milestone_id:
            return stop(f"reached --until {milestone_id} ({status}); not running it", EXIT_STOPPED)
        if iteration >= args.max:
            return stop(f"reached --max {args.max} iterations; next is {milestone_id} ({status})", EXIT_STOPPED)

        iteration += 1
        head_before = head(root)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        name = f"implement-loop {milestone_id} #{iteration} {stamp} {os.getpid()}"
        try:
            session_id = run_session(args, root, name, f"[{iteration}] {milestone_id} ({status})")
        except SessionError as error:
            return stop(str(error), EXIT_ERROR)

        head_after = head(root)
        try:
            after_state, after_digest = read_state(root)
        except StateError as error:
            print(f"[{iteration}] {milestone_id}: {status} -> ?, HEAD {short(head_before)} -> {short(head_after)}")
            return stop(str(error), EXIT_ERROR)
        print(
            f"[{iteration}] {milestone_id}: {status} -> {status_of(after_state, milestone_id)}, "
            f"HEAD {short(head_before)} -> {short(head_after)} (session {session_id})",
            flush=True,
        )
        if after_digest == digest and head_after == head_before:
            return stop(
                f"iteration {iteration} changed neither {STATE} nor HEAD on {milestone_id}; "
                f"it is waiting on something the loop cannot provide -- claude attach {session_id} to see what",
                EXIT_STOPPED,
            )
        state, digest = after_state, after_digest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-invoke /harness:implement in a fresh background session until a stop condition."
    )
    parser.add_argument("--until", metavar="MILESTONE", help="stop once this milestone becomes current, before running it")
    parser.add_argument("--max", type=int, default=DEFAULT_MAX, help=f"maximum iterations (default {DEFAULT_MAX})")
    parser.add_argument(
        "--permission-mode",
        choices=PERMISSION_MODES,
        default=DEFAULT_PERMISSION_MODE,
        help=f"passed to claude (default {DEFAULT_PERMISSION_MODE})",
    )
    parser.add_argument("--plugin-dir", type=Path, help="passed to claude, so each session loads this harness")
    args = parser.parse_args()
    if args.max < 1:
        parser.error("--max must be at least 1")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
