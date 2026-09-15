#!/usr/bin/env python3
"""Record and inspect resumable long external jobs without polling."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def root_for(state_path: Path) -> Path:
    return state_path.parent.parent if state_path.parent.name == ".harness" else state_path.parent


def load_state(path: Path) -> dict:
    try:
        state = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read state: {error}") from error
    if state.get("schema_version") != 2:
        raise ValueError("external jobs require schema_version 2")
    return state


def milestone(state: dict, milestone_id: str) -> dict:
    value = state.get("milestones", {}).get(milestone_id)
    if not isinstance(value, dict):
        raise ValueError(f"milestone {milestone_id!r} is absent from state")
    if value.get("status") != "IN_PROGRESS":
        raise ValueError("external jobs require an IN_PROGRESS milestone")
    return value


def safe_artifact(state_path: Path, artifact: str) -> Path:
    if not artifact.startswith(".harness/evidence/"):
        raise ValueError("external job results must be under .harness/evidence/")
    root = root_for(state_path).resolve()
    candidate = (root / artifact).resolve()
    if root not in candidate.parents:
        raise ValueError("external job result escapes the repository")
    return candidate


def persist(path: Path, state: dict) -> None:
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def validate_written(args, original: str) -> None:
    command = [sys.executable, str(Path(__file__).with_name("check-state.py")),
               str(args.state), "--milestones", str(args.milestones)]
    if args.requirements:
        command.extend(["--requirements", str(args.requirements)])
    checked = subprocess.run(command, text=True, capture_output=True, check=False)
    if checked.returncode:
        args.state.write_text(original)
        raise ValueError("external job state failed validation: " + checked.stderr.strip())


def launch(args, state: dict, active: dict) -> str:
    approved = state.get("approved_external_job_classes", [])
    if args.job_class not in approved:
        raise ValueError(f"external job class {args.job_class!r} is not approved in state")
    safe_artifact(args.state, args.result_artifact)
    jobs = active.setdefault("external_jobs", [])
    if any(isinstance(job, dict) and job.get("id") == args.job_id for job in jobs):
        raise ValueError(f"external job {args.job_id!r} already exists; refusing duplicate launch")
    jobs.append({
        "id": args.job_id,
        "class": args.job_class,
        "owner": args.owner,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "result_artifact": args.result_artifact,
        "status": "RUNNING",
    })
    return "WAITING_EXTERNAL"


def inspect(args, state: dict, active: dict) -> tuple[str, bool]:
    job = next(
        (item for item in active.get("external_jobs", [])
         if isinstance(item, dict) and item.get("id") == args.job_id),
        None,
    )
    if not job:
        raise ValueError(f"external job {args.job_id!r} is absent")
    if job.get("status") in {"COMPLETE", "FAILED"}:
        return job["status"], False
    result_path = safe_artifact(args.state, job["result_artifact"])
    if not result_path.exists():
        return "WAITING_EXTERNAL", False
    try:
        result = json.loads(result_path.read_text())
    except json.JSONDecodeError:
        return "WAITING_EXTERNAL", False
    if not isinstance(result, dict) or result.get("complete") is not True:
        return "WAITING_EXTERNAL", False
    if result.get("status") not in {"COMPLETE", "FAILED"}:
        raise ValueError("terminal external result status must be COMPLETE or FAILED")
    if not isinstance(result.get("summary"), str) or not result.get("summary"):
        raise ValueError("terminal external result requires a non-empty summary")
    job["status"] = result["status"]
    job["finished_at"] = datetime.now(timezone.utc).isoformat()
    job["result_sha256"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
    job["summary"] = result["summary"]
    return job["status"], True


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="action", required=True)
    for action in ("launch", "inspect"):
        command = commands.add_parser(action)
        command.add_argument("--state", required=True, type=Path)
        command.add_argument("--milestones", required=True, type=Path)
        command.add_argument("--requirements", type=Path)
        command.add_argument("--milestone", required=True)
        command.add_argument("--job-id", required=True)
        if action == "launch":
            command.add_argument("--job-class", required=True)
            command.add_argument("--owner", required=True)
            command.add_argument("--result-artifact", required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        original = args.state.read_text()
        state = load_state(args.state)
        active = milestone(state, args.milestone)
        if args.action == "launch":
            status = launch(args, state, active)
            changed = True
        else:
            status, changed = inspect(args, state, active)
        if changed:
            persist(args.state, state)
            validate_written(args, original)
        print(f"{status}: {args.job_id}")
        return 0
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
