#!/usr/bin/env python3
"""Validate harness state and its human-facing milestone index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


STATUSES = {"TODO", "IN_PROGRESS", "REVIEW", "DONE", "BLOCKED", "DEFERRED"}
CRITERION_STATUSES = {"PENDING", "PASS", "FAIL", "DEFERRED"}
BLOCKING_SEVERITIES = {"BLOCKER", "IMPORTANT"}
TIERS = {"Cheap", "Mid", "Top"}


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read valid JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError("state root must be an object")
    return value


def markdown_statuses(path: Path) -> dict[str, str]:
    text = path.read_text()
    headings = list(re.finditer(r"(?m)^## (M[^ ]+)\s+—.*$", text))
    result = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.end():end]
        status = re.search(r"(?m)^Status:\s*([A-Z_]+)\s*$", section)
        if status:
            result[heading.group(1)] = status.group(1)
    return result


def validate(
    state: dict,
    state_path: Path,
    milestones_path: Path | None,
    all_done: bool,
    record_only: tuple[str, str] | None,
) -> list[str]:
    errors = []
    if state.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    milestones = state.get("milestones")
    if not isinstance(milestones, dict) or not milestones:
        return errors + ["milestones must be a non-empty object"]

    current = state.get("current_milestone")
    if current is not None and current not in milestones:
        errors.append(f"current_milestone {current!r} is not present")

    for milestone_id, milestone in milestones.items():
        prefix = f"milestones.{milestone_id}"
        if not isinstance(milestone, dict):
            errors.append(f"{prefix} must be an object")
            continue
        status = milestone.get("status")
        if status not in STATUSES:
            errors.append(f"{prefix}.status is invalid: {status!r}")
        cycles = milestone.get("review_cycles")
        if not isinstance(cycles, int) or cycles < 0:
            errors.append(f"{prefix}.review_cycles must be a non-negative integer")
        elif cycles > 2 and not milestone.get("review_override"):
            errors.append(f"{prefix} exceeds two review cycles without a named override")

        criteria = milestone.get("criteria", [])
        if not isinstance(criteria, list):
            errors.append(f"{prefix}.criteria must be an array")
            criteria = []
        criterion_ids = set()
        for criterion in criteria:
            if not isinstance(criterion, dict) or not criterion.get("id"):
                errors.append(f"{prefix} contains a criterion without an id")
                continue
            criterion_id = criterion["id"]
            if criterion_id in criterion_ids:
                errors.append(f"{prefix} repeats criterion id {criterion_id}")
            criterion_ids.add(criterion_id)
            if criterion.get("status") not in CRITERION_STATUSES:
                errors.append(f"{prefix}.{criterion_id} has invalid status")
            if status == "DONE" and criterion.get("status") != "PASS":
                errors.append(f"{prefix} is DONE but {criterion_id} is not PASS")

        unresolved = [
            finding.get("id", "<missing id>")
            for finding in milestone.get("findings", [])
            if isinstance(finding, dict)
            and finding.get("severity") in BLOCKING_SEVERITIES
            and finding.get("status") != "RESOLVED"
        ]
        if status == "DONE" and unresolved:
            errors.append(f"{prefix} is DONE with unresolved findings: {', '.join(unresolved)}")

        for field in ("tasks", "reviews", "validation", "follow_ups"):
            if not isinstance(milestone.get(field, []), list):
                errors.append(f"{prefix}.{field} must be an array")
        for field in ("tasks", "reviews", "validation"):
            for entry in milestone.get(field, []):
                artifact = entry.get("artifact") if isinstance(entry, dict) else None
                if artifact and not (state_path.parent.parent / artifact).exists():
                    errors.append(f"{prefix}.{field} names missing artifact {artifact}")

        as_built = milestone.get("as_built")
        if as_built is not None and not isinstance(as_built, dict):
            errors.append(f"{prefix}.as_built must be an object")
        elif isinstance(as_built, dict):
            artifact = as_built.get("artifact")
            if artifact and not (state_path.parent.parent / artifact).exists():
                errors.append(f"{prefix}.as_built names missing artifact {artifact}")

        for task in milestone.get("tasks", []):
            if not isinstance(task, dict):
                errors.append(f"{prefix}.tasks entries must be objects")
                continue
            routing = task.get("routing")
            if not isinstance(routing, dict):
                errors.append(f"{prefix}.tasks entry lacks structured routing")
                continue
            tier = routing.get("tier")
            if tier not in TIERS:
                errors.append(f"{prefix}.tasks entry has invalid routing tier {tier!r}")
            if not routing.get("model") or not routing.get("reason_code"):
                errors.append(f"{prefix}.tasks entry lacks model or reason_code")
            if tier == "Top" and not routing.get("detail"):
                errors.append(f"{prefix}.tasks Top routing requires a named detail")

        for review in milestone.get("reviews", []):
            if not isinstance(review, dict):
                errors.append(f"{prefix}.reviews entries must be objects")
                continue
            if review.get("scope") == "RECORD_ONLY":
                errors.append(f"{prefix}.reviews must not contain a record-only semantic review")
            if review.get("tier") not in {"Mid", "Top"}:
                errors.append(f"{prefix}.reviews entry must record Mid or Top tier")
            if not review.get("diff_range") or not review.get("reason_code"):
                errors.append(f"{prefix}.reviews entry lacks diff_range or reason_code")

    requirements = state.get("requirements", {})
    if not isinstance(requirements, dict):
        errors.append("requirements must be an object mapping ids to milestone ids")
    else:
        for requirement, owner in requirements.items():
            if owner not in milestones:
                errors.append(f"requirement {requirement} has unknown owner {owner}")

    if milestones_path:
        try:
            markdown = markdown_statuses(milestones_path)
        except OSError as error:
            errors.append(f"cannot read milestone index: {error}")
        else:
            for milestone_id, milestone in milestones.items():
                if markdown.get(milestone_id) != milestone.get("status"):
                    errors.append(
                        f"index mismatch for {milestone_id}: "
                        f"state={milestone.get('status')} markdown={markdown.get(milestone_id)}"
                    )

    if all_done:
        if not requirements:
            errors.append("all-DONE check requires explicit requirement ownership")
        unfinished = [key for key, value in milestones.items() if value.get("status") != "DONE"]
        if unfinished:
            errors.append("all-DONE check has unfinished milestones: " + ", ".join(unfinished))
        if current is not None:
            errors.append("all-DONE check requires current_milestone to be null")
    if record_only:
        repository = state_path.parent.parent
        completed = subprocess.run(
            ["git", "-C", str(repository), "diff", "--name-only", *record_only],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            errors.append("record-only diff could not be read: " + completed.stderr.strip())
        else:
            substantive = [
                path for path in completed.stdout.splitlines()
                if path and not path.startswith(".harness/")
            ]
            if substantive:
                errors.append("record-only correction changed substantive paths: " + ", ".join(substantive))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("state", type=Path)
    parser.add_argument("--milestones", type=Path)
    parser.add_argument("--all-done", action="store_true")
    parser.add_argument("--record-only", nargs=2, metavar=("BASE", "HEAD"))
    args = parser.parse_args()
    try:
        state = load(args.state)
        errors = validate(
            state,
            args.state,
            args.milestones,
            args.all_done,
            tuple(args.record_only) if args.record_only else None,
        )
    except ValueError as error:
        errors = [str(error)]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {len(state['milestones'])} milestone(s), state schema v1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
