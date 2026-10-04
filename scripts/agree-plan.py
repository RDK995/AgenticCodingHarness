#!/usr/bin/env python3
"""Record a human's agreement to one or more milestones' DRAFT task plans.

Sets the plan to AGREED in all three places it is recorded -- structured state,
the plan file's Status line, and the milestone's ### Plan field in the human
index -- then runs the normal state check. Refuses anything but a TODO
milestone with a DRAFT plan whose tasks each name a packet on disk, and any
plan in which two tasks free to run at the same time may change the same file.
"""

from __future__ import annotations

import argparse
import fnmatch
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


def plan_after(plan_text: str, milestone_id: str) -> dict[str, list[str]]:
    """Each task's `After` entries, from the plan's `## Tasks` table."""
    section = re.search(r"(?ms)^## Tasks\s*$(.*?)(?=^## |\Z)", plan_text)
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in (section.group(1) if section else "").splitlines()
        if line.strip().startswith("|") and not re.fullmatch(r"[|\s:-]+", line.strip())
    ]
    if not rows or "After" not in rows[0] or "Task" not in rows[0]:
        return {}
    task_col, after_col = rows[0].index("Task"), rows[0].index("After")
    after = {}
    for row in rows[1:]:
        if len(row) <= max(task_col, after_col):
            continue
        ids = re.findall(r"(?:M[^\s,|`]*-)?T\d+[a-z]?", row[after_col])
        after[row[task_col]] = [i if i.startswith("M") else f"{milestone_id}-{i}" for i in ids]
    return after


def allowed_files(packet_text: str) -> list[str] | None:
    """The packet's `Files Allowed To Change` list, or None if it has none."""
    lines = packet_text.splitlines()
    for index, line in enumerate(lines):
        if re.fullmatch(r"\s*(?:#+\s*)?Files Allowed To Change:?\s*", line):
            paths = []
            for item in lines[index + 1:]:
                bullet = re.match(r"\s*[-*]\s+`?([^`\s]+)`?", item)
                if bullet:
                    paths.append(bullet.group(1).removeprefix("./").rstrip("/"))
                elif item.strip():
                    break
            return paths
    return None


def overlaps(a: str, b: str) -> bool:
    if any(c in a + b for c in "*?["):
        return fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a)
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def parallel_conflicts(state: dict, root: Path, milestone_id: str) -> list[str]:
    """Tasks free to run at the same time must not share a file they may change.

    The implementation phase starts every task whose `After` tasks are accepted,
    all in one working tree. Two of them allowed to change the same file would
    edit it at once and each be blamed for the other's edit, so a shared file
    must put one task `After` the other.
    """
    milestone = state["milestones"][milestone_id]
    tasks = [task["id"] for task in milestone["tasks"]]
    if len(tasks) < 2:
        return []
    plan_text = (root / milestone["plan"]["artifact"]).read_text()
    after = plan_after(plan_text, milestone_id)
    errors = [
        f"{milestone_id} task {task} is After {dep}, which is not a task in the plan"
        for task, deps in after.items() for dep in deps if dep not in tasks
    ]

    def before(task: str) -> set[str]:
        seen, stack = set(), list(after.get(task, []))
        while stack:
            dep = stack.pop()
            if dep not in seen:
                seen.add(dep)
                stack.extend(after.get(dep, []))
        return seen

    ancestors = {task: before(task) for task in tasks}
    files = {task["id"]: allowed_files((root / task["artifact"]).read_text()) for task in milestone["tasks"]}
    for i, first in enumerate(tasks):
        for second in tasks[i + 1:]:
            if first in ancestors[second] or second in ancestors[first]:
                continue
            for task in (first, second):
                if files[task] is None:
                    errors.append(
                        f"{milestone_id} task {task} can run alongside {second if task == first else first} "
                        "but its packet names no Files Allowed To Change"
                    )
            shared = sorted({a for a in files[first] or [] for b in files[second] or [] if overlaps(a, b)})
            if shared:
                errors.append(
                    f"{milestone_id} tasks {first} and {second} can run at the same time but may both change "
                    f"{', '.join(shared)}; put one After the other"
                )
    return list(dict.fromkeys(errors))


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


def out_of_order(state: dict, agreeing: list[str]) -> str | None:
    """A TODO milestone ahead of one being agreed must be agreed already, or now.

    The loop stops at the first TODO milestone without an agreed plan, and a
    later plan is written against the earlier ones, so agreeing past a gap
    agrees a plan whose foundations nobody has agreed.
    """
    pending = []
    for milestone_id, milestone in state.get("milestones", {}).items():
        if milestone_id in agreeing:
            if pending:
                return f"cannot agree {milestone_id} before {', '.join(pending)}, which come first and are not agreed"
            continue
        plan = milestone.get("plan") if isinstance(milestone, dict) else None
        agreed = isinstance(plan, dict) and plan.get("status") == "AGREED"
        if isinstance(milestone, dict) and milestone.get("status") == "TODO" and not agreed:
            pending.append(milestone_id)
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("state", type=Path)
    parser.add_argument("milestone", nargs="+", help="the milestones whose DRAFT plans the human agreed")
    parser.add_argument("--milestones", type=Path, required=True)
    parser.add_argument("--requirements", type=Path)
    parser.add_argument("--check", action="store_true",
                        help="only check which tasks can run together; write nothing")
    args = parser.parse_args()
    root = args.state.resolve().parent.parent
    try:
        state = check_state.load(args.state)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    reasons = [reason for reason in (refusal(state, root, m) for m in args.milestone) if reason]
    if not args.check:
        reasons += [reason for reason in [out_of_order(state, args.milestone)] if reason]
    if not reasons:
        reasons += [reason for m in args.milestone for reason in parallel_conflicts(state, root, m)]
    if reasons:
        for reason in reasons:
            print(f"ERROR: {reason}", file=sys.stderr)
        return 1
    if args.check:
        print(f"OK: tasks that can run at the same time share no file in {', '.join(args.milestone)}")
        return 0

    # Everything is computed before anything is written: all or nothing.
    plan_texts = {}
    try:
        index_text = args.milestones.read_text()
    except OSError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for milestone_id in args.milestone:
        plan = state["milestones"][milestone_id]["plan"]
        plan_path = root / plan["artifact"]
        plan_text, count = re.subn(r"(?m)^Status:\s*DRAFT\s*$", "Status: AGREED", plan_path.read_text(), count=1)
        if not count:
            print(f"ERROR: {plan['artifact']} has no 'Status: DRAFT' line", file=sys.stderr)
            return 1
        plan_texts[plan_path] = plan_text
        try:
            index_text = set_plan_field(index_text, milestone_id, f"`{plan['artifact']}` — AGREED")
        except ValueError as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 1
        plan["status"] = "AGREED"

    errors = check_state.validate(state, args.state, args.milestones, False, None, args.requirements)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    args.state.write_text(json.dumps(state, indent=2) + "\n")
    for plan_path, plan_text in plan_texts.items():
        plan_path.write_text(plan_text)
    args.milestones.write_text(index_text)
    print(f"OK: plans AGREED for {', '.join(args.milestone)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
