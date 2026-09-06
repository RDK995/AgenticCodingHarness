#!/usr/bin/env python3
"""Create v1 structured state from an existing milestones.md file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from requirements_ids import functional_requirement_ids


def derive_ownership(requirement_ids, milestone_sections, supplied=None):
    supplied = supplied or {}
    milestones = set(milestone_sections)
    unknown_requirements = sorted(set(supplied) - requirement_ids)
    unknown_milestones = sorted(
        f"{requirement}={owner}"
        for requirement, owner in supplied.items()
        if owner not in milestones
    )
    if unknown_requirements:
        raise ValueError(
            "ownership map contains ids absent from requirements: "
            + ", ".join(unknown_requirements)
        )
    if unknown_milestones:
        raise ValueError(
            "ownership map names unknown milestones: " + ", ".join(unknown_milestones)
        )

    ownership = {}
    ambiguous = []
    for requirement in sorted(requirement_ids):
        if requirement in supplied:
            ownership[requirement] = supplied[requirement]
            continue
        referenced_by = [
            milestone_id
            for milestone_id, section in milestone_sections.items()
            if re.search(rf"\b{re.escape(requirement)}\b", section, re.IGNORECASE)
        ]
        if len(referenced_by) == 1:
            ownership[requirement] = referenced_by[0]
        elif len(milestones) == 1:
            ownership[requirement] = next(iter(milestones))
        else:
            ambiguous.append(requirement)
    if ambiguous:
        raise ValueError(
            "cannot infer one owning milestone for "
            + ", ".join(ambiguous)
            + "; pass --ownership <json> with an explicit id-to-milestone map"
        )
    return ownership


def migrate(text: str, requirement_ids: set[str], supplied_ownership=None) -> dict:
    headings = list(re.finditer(r"(?m)^## (M[^ ]+)\s+—\s*(.+)$", text))
    milestones = {}
    milestone_sections = {}
    for index, heading in enumerate(headings):
        milestone_id, outcome = heading.group(1), heading.group(2).strip()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.end():end]
        milestone_sections[milestone_id] = f"{outcome}\n{section}"
        status_match = re.search(r"(?m)^Status:\s*([A-Z_]+)\s*$", section)
        cycles_match = re.search(r"(?ms)^### Review Cycles\s*\n+\s*(\d+)", section)
        baseline_match = re.search(r"(?ms)^### Baseline\s*\n+\s*([^\n]+)", section)
        as_built_match = re.search(
            r"(?ms)^### As-Built\s*\n(.*?)(?=^### |^## |\Z)", section
        )
        criteria = []
        criteria_match = re.search(
            r"(?ms)^### Acceptance Criteria\s*\n(.*?)(?=^### |^## |\Z)", section
        )
        if criteria_match:
            for number, item in enumerate(
                re.finditer(r"(?m)^- \[([ xX])\]\s*(.+)$", criteria_match.group(1)), 1
            ):
                criteria.append(
                    {
                        "id": f"{milestone_id}-AC{number}",
                        "status": "PASS" if item.group(1).lower() == "x" else "PENDING",
                        "text": item.group(2).strip(),
                        "evidence": [],
                    }
                )
        baseline = baseline_match.group(1).strip() if baseline_match else ""
        commit, _, branch = baseline.partition(" on ")
        as_built_text = as_built_match.group(1).strip() if as_built_match else ""
        as_built_artifact = re.search(r"\.harness/as-built/[^\s`)]+", as_built_text)
        milestones[milestone_id] = {
            "outcome": outcome,
            "status": status_match.group(1) if status_match else "TODO",
            "review_cycles": int(cycles_match.group(1)) if cycles_match else 0,
            "review_override": None,
            "baseline": {"commit": commit, "branch": branch},
            "as_built": {
                "artifact": as_built_artifact.group(0) if as_built_artifact else None,
                "result": as_built_text or "PENDING",
            },
            "criteria": criteria,
            "tasks": [],
            "reviews": [],
            "findings": [],
            "validation": [],
            "follow_ups": [],
        }
    current = next(
        (key for key, value in milestones.items() if value["status"] not in {"DONE", "DEFERRED"}),
        None,
    )
    return {
        "schema_version": 1,
        "current_milestone": current,
        "requirements": derive_ownership(
            requirement_ids, milestone_sections, supplied_ownership
        ),
        "milestones": milestones,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("milestones", type=Path)
    parser.add_argument("state", type=Path)
    parser.add_argument("--requirements", required=True, type=Path)
    parser.add_argument(
        "--ownership",
        type=Path,
        help="JSON object mapping requirement ids to milestone ids when inference is ambiguous",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.state.exists() and not args.force:
        parser.error(f"refusing to overwrite {args.state}; pass --force deliberately")
    try:
        requirements_text = args.requirements.read_text()
    except OSError as error:
        parser.error(f"cannot read requirements document: {error}")
    requirement_ids, requirement_errors = functional_requirement_ids(requirements_text)
    if requirement_errors:
        parser.error("; ".join(requirement_errors))
    supplied_ownership = None
    if args.ownership:
        try:
            supplied_ownership = json.loads(args.ownership.read_text())
        except (OSError, json.JSONDecodeError) as error:
            parser.error(f"cannot read ownership map: {error}")
        if not isinstance(supplied_ownership, dict):
            parser.error("ownership map must be a JSON object")
    try:
        state = migrate(
            args.milestones.read_text(), requirement_ids, supplied_ownership
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if not state["milestones"]:
        parser.error("no milestone sections found")
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Wrote {args.state} with {len(state['milestones'])} milestone(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
