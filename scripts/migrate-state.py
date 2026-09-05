#!/usr/bin/env python3
"""Create v1 structured state from an existing milestones.md file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


def migrate(text: str) -> dict:
    headings = list(re.finditer(r"(?m)^## (M[^ ]+)\s+—\s*(.+)$", text))
    milestones = {}
    for index, heading in enumerate(headings):
        milestone_id, outcome = heading.group(1), heading.group(2).strip()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.end():end]
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
        "requirements": {},
        "milestones": milestones,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("milestones", type=Path)
    parser.add_argument("state", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.state.exists() and not args.force:
        parser.error(f"refusing to overwrite {args.state}; pass --force deliberately")
    state = migrate(args.milestones.read_text())
    if not state["milestones"]:
        parser.error("no milestone sections found")
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Wrote {args.state} with {len(state['milestones'])} milestone(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
