#!/usr/bin/env python3
"""Record a human's agreement to a milestone's DRAFT task plan.

Sets the plan to AGREED in all three places it is recorded -- structured state,
the plan file's Status line, and the milestone's ### Plan field in the human
index -- then runs the normal state check. Refuses anything but a TODO
milestone with a DRAFT plan whose tasks each name a packet on disk.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location(
    "check_state", Path(__file__).resolve().parent / "check-state.py"
)
check_state = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_state)


def refusal(state: dict, root: Path, milestone_id: str) -> str | None:
    milestone = state.get("milestones", {}).get(milestone_id)
    if not isinstance(milestone, dict):
        return f"{milestone_id} is not a milestone in state"
    if milestone.get("status") != "TODO":
        return f"{milestone_id} is {milestone.get('status')}, not TODO"
    plan = milestone.get("plan")
    if not isinstance(plan, dict) or plan.get("status") != "DRAFT":
        return f"{milestone_id} has no DRAFT plan to agree"
    artifact = plan.get("artifact")
    if not artifact or not (root / artifact).is_file():
        return f"{milestone_id} plan file {artifact!r} does not exist"
    tasks = milestone.get("tasks") or []
    if not tasks:
        return f"{milestone_id} plan has no tasks"
    for task in tasks:
        packet = task.get("artifact") if isinstance(task, dict) else None
        if not packet or not (root / packet).is_file():
            return f"{milestone_id} task {task.get('id') if isinstance(task, dict) else task!r} has no packet on disk"
    return None


def set_plan_field(text: str, milestone_id: str, value: str) -> str:
    headings = list(re.finditer(r"(?m)^## (M[^ ]+)\s+—.*$", text))
    for index, heading in enumerate(headings):
        if heading.group(1) != milestone_id:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.end():end]
        field = re.search(r"(?m)^### Plan\n(?:(?!###|## ).*\n)*", section)
        replacement = f"### Plan\n{value}\n\n"
        if field:
            section = section[:field.start()] + replacement + section[field.end():]
        else:
            baseline = re.search(r"(?m)^### Baseline$", section)
            if not baseline:
                raise ValueError(f"{milestone_id} has neither ### Plan nor ### Baseline")
            section = section[:baseline.start()] + replacement + section[baseline.start():]
        return text[:heading.end()] + section + text[end:]
    raise ValueError(f"{milestone_id} has no section in the milestone index")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("state", type=Path)
    parser.add_argument("milestone")
    parser.add_argument("--milestones", type=Path, required=True)
    parser.add_argument("--requirements", type=Path)
    args = parser.parse_args()
    root = args.state.resolve().parent.parent
    try:
        state = check_state.load(args.state)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    reason = refusal(state, root, args.milestone)
    if reason:
        print(f"ERROR: {reason}", file=sys.stderr)
        return 1

    plan = state["milestones"][args.milestone]["plan"]
    plan_path = root / plan["artifact"]
    plan_text, count = re.subn(r"(?m)^Status:\s*DRAFT\s*$", "Status: AGREED", plan_path.read_text(), count=1)
    if not count:
        print(f"ERROR: {plan['artifact']} has no 'Status: DRAFT' line", file=sys.stderr)
        return 1
    try:
        index_text = set_plan_field(args.milestones.read_text(), args.milestone, f"`{plan['artifact']}` — AGREED")
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    plan["status"] = "AGREED"
    errors = check_state.validate(state, args.state, args.milestones, False, None, args.requirements)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    args.state.write_text(json.dumps(state, indent=2) + "\n")
    plan_path.write_text(plan_text)
    args.milestones.write_text(index_text)
    print(f"OK: {args.milestone} plan AGREED ({plan['artifact']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
