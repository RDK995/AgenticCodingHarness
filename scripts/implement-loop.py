#!/usr/bin/env python3
"""Run /harness:implement repeatedly, each time in a brand-new headless session.

A fresh `claude -p` process is the `/clear` the implement skill asks the human
for at every milestone boundary. Whether to run again is decided from repository
state alone -- `.harness/state.json` and `git rev-parse HEAD` -- never from what
the session said.

Run from the project root. Exit status:
  0  every milestone is DONE
  3  stopped by a condition: a BLOCKED milestone, a status the implement skill
     has no branch for, no progress, --until reached, or --max reached
  1  error: the claude process exited non-zero, or state could not be read
  2  bad usage
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

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
LOG_DIR = Path(".harness/evidence/implement-loop")


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


def log_dir(root: Path) -> Path:
    directory = root / LOG_DIR
    directory.mkdir(parents=True, exist_ok=True)
    # Keep the logs out of git: an untracked file here would otherwise be swept
    # into the next milestone branch's first commit by the implement skill.
    ignore = directory / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n")
    return directory


def command(args: argparse.Namespace) -> list[str]:
    argv = [
        "claude",
        "-p",
        "/harness:implement",
        "--permission-mode",
        args.permission_mode,
        # Nobody is there to answer a prompt: deny it instead of waiting.
        "--permission-prompts",
        "none",
        "--output-format",
        "text",
    ]
    if args.plugin_dir:
        argv += ["--plugin-dir", str(args.plugin_dir)]
    return argv


def stop(reason: str, code: int) -> int:
    print(f"STOP: {reason}", flush=True)
    return code


def run(args: argparse.Namespace) -> int:
    root = Path.cwd()
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
    while True:
        selected = select(state)
        if selected is None:
            return stop("all milestones are DONE", EXIT_ALL_DONE)
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
        log_path = log_dir(root) / f"{stamp}-{iteration}.log"
        argv = command(args)
        with log_path.open("w") as log:
            log.write(f"$ {' '.join(argv)}\n")
            log.flush()
            try:
                completed = subprocess.run(
                    argv, cwd=root, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, check=False
                )
            except OSError as error:
                return stop(f"could not start claude: {error}", EXIT_ERROR)
            log.write(f"\n[exit status {completed.returncode}]\n")

        head_after = head(root)
        try:
            after_state, after_digest = read_state(root)
        except StateError as error:
            print(f"[{iteration}] {milestone_id}: {status} -> ?, HEAD {short(head_before)} -> {short(head_after)} ({log_path.relative_to(root)})")
            return stop(str(error), EXIT_ERROR)
        print(
            f"[{iteration}] {milestone_id}: {status} -> {status_of(after_state, milestone_id)}, "
            f"HEAD {short(head_before)} -> {short(head_after)} ({log_path.relative_to(root)})",
            flush=True,
        )
        if completed.returncode != 0:
            return stop(f"claude exited with status {completed.returncode}; see {log_path.relative_to(root)}", EXIT_ERROR)
        if after_digest == digest and head_after == head_before:
            return stop(
                f"iteration {iteration} changed neither {STATE} nor HEAD on {milestone_id}; "
                f"it is waiting on something the loop cannot provide -- see {log_path.relative_to(root)}",
                EXIT_STOPPED,
            )
        state, digest = after_state, after_digest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-invoke /harness:implement in a fresh headless session until a stop condition."
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
