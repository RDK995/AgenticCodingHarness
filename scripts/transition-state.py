#!/usr/bin/env python3
"""Apply guarded, atomic schema-v2 milestone state transitions."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from requirements_ids import milestone_headings
from review_result import criterion_statuses, load_result, validate_result


def project_root(state_path: Path) -> Path:
    return state_path.parent.parent if state_path.parent.name == ".harness" else state_path.parent


def load_state(path: Path) -> dict:
    try:
        state = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read valid state JSON: {error}") from error
    if not isinstance(state, dict):
        raise ValueError("state root must be an object")
    if state.get("schema_version") != 2:
        raise ValueError("guarded transitions require schema_version 2")
    return state


def get_milestone(state: dict, milestone_id: str) -> dict:
    milestone = state.get("milestones", {}).get(milestone_id)
    if not isinstance(milestone, dict):
        raise ValueError(f"milestone {milestone_id!r} is absent from state")
    return milestone


def criterion_ids(milestone: dict) -> set[str]:
    ids = {
        item.get("id")
        for item in milestone.get("criteria", [])
        if isinstance(item, dict) and item.get("id")
    }
    if not ids or len(ids) != len(milestone.get("criteria", [])):
        raise ValueError("milestone criteria must have unique, non-empty ids")
    return ids


def result_relative_path(state_path: Path, result_path: Path) -> str:
    root = project_root(state_path).resolve()
    candidate = result_path.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("review result must be stored inside the project repository")
    return candidate.relative_to(root).as_posix()


def update_markdown(text: str, milestone_id: str, milestone: dict) -> str:
    headings = milestone_headings(text)
    target_index = next(
        (index for index, heading in enumerate(headings) if heading.group("id") == milestone_id),
        None,
    )
    if target_index is None:
        raise ValueError(f"milestone index has no section for {milestone_id}")
    heading = headings[target_index]
    end = headings[target_index + 1].start() if target_index + 1 < len(headings) else len(text)
    section = text[heading.end():end]
    status_match = re.search(r"(?m)^Status:\s*([A-Z_]+)\s*$", section)
    if not status_match:
        raise ValueError(f"milestone {milestone_id} has no Status field")
    section = (
        section[:status_match.start(1)]
        + milestone["status"]
        + section[status_match.end(1):]
    )

    criteria_match = re.search(
        r"(?ms)^### Acceptance Criteria\s*\n(?P<body>.*?)(?=^### |^## |\Z)",
        section,
    )
    if not criteria_match:
        raise ValueError(f"milestone {milestone_id} has no Acceptance Criteria section")
    items = list(re.finditer(r"(?m)^(?P<prefix>\s*-\s*\[)(?P<mark>[ xX])(?P<rest>\]\s*.+)$", criteria_match.group("body")))
    state_criteria = milestone.get("criteria", [])
    if len(items) != len(state_criteria):
        raise ValueError(
            f"criterion count mismatch for {milestone_id}: "
            f"state={len(state_criteria)} markdown={len(items)}"
        )
    body = criteria_match.group("body")
    pieces, cursor = [], 0
    for item, criterion in zip(items, state_criteria):
        pieces.append(body[cursor:item.start("mark")])
        pieces.append("x" if criterion.get("status") == "PASS" else " ")
        cursor = item.end("mark")
    pieces.append(body[cursor:])
    new_body = "".join(pieces)
    section = (
        section[:criteria_match.start("body")]
        + new_body
        + section[criteria_match.end("body"):]
    )
    cycles_match = re.search(
        r"(?ms)(^### Review Cycles\s*\n+\s*)(\d+)(\s*$|\s*\n)", section
    )
    cycles = str(milestone.get("review_cycles", 0))
    if cycles_match:
        section = (
            section[:cycles_match.start(2)]
            + cycles
            + section[cycles_match.end(2):]
        )
    else:
        section = section.rstrip() + f"\n\n### Review Cycles\n\n{cycles}\n"
    return text[:heading.end()] + section + text[end:]


def write_temporary(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    with os.fdopen(descriptor, "w") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    return temporary


def persist_and_validate(
    state_path: Path,
    milestones_path: Path,
    requirements_path: Path | None,
    state: dict,
    milestone_id: str,
) -> None:
    original_state = state_path.read_text()
    original_milestones = milestones_path.read_text()
    updated_milestones = update_markdown(
        original_milestones, milestone_id, state["milestones"][milestone_id]
    )
    state_text = json.dumps(state, indent=2) + "\n"
    state_temp = write_temporary(state_path, state_text)
    milestones_temp = write_temporary(milestones_path, updated_milestones)
    try:
        state_temp.replace(state_path)
        milestones_temp.replace(milestones_path)
        command = [
            sys.executable,
            str(Path(__file__).with_name("check-state.py")),
            str(state_path),
            "--milestones",
            str(milestones_path),
        ]
        if requirements_path:
            command.extend(["--requirements", str(requirements_path)])
        checked = subprocess.run(command, text=True, capture_output=True, check=False)
        if checked.returncode:
            raise ValueError("post-transition state validation failed: " + checked.stderr.strip())
    except Exception:
        state_path.write_text(original_state)
        milestones_path.write_text(original_milestones)
        raise
    finally:
        state_temp.unlink(missing_ok=True)
        milestones_temp.unlink(missing_ok=True)


def enter_review(state: dict, milestone_id: str, head: str, base: str | None) -> None:
    milestone = get_milestone(state, milestone_id)
    if milestone.get("status") not in {"TODO", "IN_PROGRESS"}:
        raise ValueError("enter-review requires TODO or IN_PROGRESS status")
    criterion_ids(milestone)
    for criterion in milestone["criteria"]:
        criterion["status"] = "PENDING"
        criterion["evidence"] = []
    baseline = milestone.get("baseline") if isinstance(milestone.get("baseline"), dict) else {}
    milestone["review_target"] = {"base": base or baseline.get("commit") or head, "head": head}
    milestone["status"] = "REVIEW"
    state["current_milestone"] = milestone_id


def apply_review(state: dict, state_path: Path, milestone_id: str, result_path: Path) -> bool:
    milestone = get_milestone(state, milestone_id)
    if milestone.get("status") != "REVIEW":
        raise ValueError("apply-review requires REVIEW status")
    target = milestone.get("review_target")
    if not isinstance(target, dict) or not target.get("head"):
        raise ValueError("apply-review requires review_target.head")
    result = load_result(result_path)
    errors = validate_result(
        result,
        milestone_id=milestone_id,
        head=target["head"],
        criterion_ids=criterion_ids(milestone),
    )
    if errors:
        raise ValueError("; ".join(errors))
    relative = result_relative_path(state_path, result_path)
    reviews = milestone.setdefault("reviews", [])
    if any(
        isinstance(review, dict) and review.get("result_artifact") == relative
        for review in reviews
    ):
        return False

    statuses = criterion_statuses(result)
    evidence = {item["id"]: item["evidence"] for item in result["criteria"]}
    for criterion in milestone["criteria"]:
        criterion["status"] = statuses[criterion["id"]]
        criterion["evidence"] = evidence[criterion["id"]]
    review = {
        "cycle": result["cycle"],
        "verdict": result["verdict"],
        "result_artifact": relative,
        "tier": result["tier"],
        "model": result["model"],
        "effort": result["effort"],
        "reason_code": result["reason_code"],
        "scope": result["scope"],
        "diff_range": f"{result['base']}...{result['head']}",
        "head": result["head"],
        "complete": True,
    }
    if result.get("report_artifact"):
        review["artifact"] = result["report_artifact"]
    reviews.append(review)

    existing = {
        item.get("id"): item
        for item in milestone.setdefault("findings", [])
        if isinstance(item, dict) and item.get("id")
    }
    for finding in result["findings"]:
        existing[finding["id"]] = finding
    milestone["findings"] = list(existing.values())

    if result["verdict"] == "PASS":
        milestone["status"] = "REVIEW"
    elif result["verdict"] == "CHANGES_REQUIRED":
        milestone["review_cycles"] = milestone.get("review_cycles", 0) + 1
        milestone["status"] = "IN_PROGRESS"
    else:
        milestone["status"] = "BLOCKED"
    return True


def reopen_after_review(state: dict, milestone_id: str) -> None:
    milestone = get_milestone(state, milestone_id)
    if milestone.get("status") not in {"REVIEW", "IN_PROGRESS"}:
        raise ValueError("reopen-after-review requires REVIEW or IN_PROGRESS status")
    milestone["status"] = "IN_PROGRESS"
    for criterion in milestone.get("criteria", []):
        criterion["status"] = "PENDING"
        criterion["evidence"] = []


def finalize(state: dict, milestone_id: str, head: str) -> None:
    milestone = get_milestone(state, milestone_id)
    if milestone.get("status") != "REVIEW":
        raise ValueError("finalize requires REVIEW status")
    target = milestone.get("review_target")
    if not isinstance(target, dict) or target.get("head") != head:
        raise ValueError("finalize HEAD does not match the reviewed HEAD")
    reviews = milestone.get("reviews", [])
    latest = reviews[-1] if reviews else None
    if not isinstance(latest, dict) or latest.get("verdict") != "PASS" or latest.get("head") != head:
        raise ValueError("finalize requires the latest terminal review to PASS the same HEAD")
    if any(item.get("status") != "PASS" for item in milestone.get("criteria", [])):
        raise ValueError("finalize requires every criterion to PASS")
    unresolved = [
        finding.get("id", "<missing id>")
        for finding in milestone.get("findings", [])
        if isinstance(finding, dict)
        and finding.get("severity") in {"BLOCKER", "IMPORTANT"}
        and finding.get("status") != "RESOLVED"
    ]
    if unresolved:
        raise ValueError("finalize has unresolved findings: " + ", ".join(unresolved))
    as_built = milestone.get("as_built")
    if not isinstance(as_built, dict) or as_built.get("result") in {None, "PENDING"}:
        raise ValueError("finalize requires a recorded as-built result or NOT_REQUIRED")
    milestone["status"] = "DONE"
    remaining = [
        key for key, value in state["milestones"].items()
        if key != milestone_id and value.get("status") not in {"DONE", "DEFERRED"}
    ]
    state["current_milestone"] = remaining[0] if remaining else None


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="action", required=True)
    for name in ("enter-review", "apply-review", "reopen-after-review", "finalize"):
        command = subparsers.add_parser(name)
        command.add_argument("--state", required=True, type=Path)
        command.add_argument("--milestones", required=True, type=Path)
        command.add_argument("--requirements", type=Path)
        command.add_argument("--milestone", required=True)
        if name in {"enter-review", "finalize"}:
            command.add_argument("--head", required=True)
        if name == "enter-review":
            command.add_argument("--base")
        if name == "apply-review":
            command.add_argument("--result", required=True, type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        state = load_state(args.state)
        changed = True
        if args.action == "enter-review":
            enter_review(state, args.milestone, args.head, args.base)
        elif args.action == "apply-review":
            changed = apply_review(state, args.state, args.milestone, args.result)
        elif args.action == "reopen-after-review":
            reopen_after_review(state, args.milestone)
        elif args.action == "finalize":
            finalize(state, args.milestone, args.head)
        if changed:
            persist_and_validate(
                args.state, args.milestones, args.requirements, state, args.milestone
            )
            print(f"OK: {args.action} applied to {args.milestone}")
        else:
            print(f"OK: {args.action} already applied to {args.milestone}")
        return 0
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
