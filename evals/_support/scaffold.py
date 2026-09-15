#!/usr/bin/env python3
"""Create tiny, isolated repositories for the runtime-v3 plugin eval cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


def run(*command: str) -> str:
    return subprocess.run(command, check=True, text=True, capture_output=True).stdout.strip()


def base_state(milestone_id: str, requirement_ids: list[str], criteria: list[str]) -> dict:
    return {
        "schema_version": 2,
        "current_milestone": milestone_id,
        "approved_external_job_classes": ["fixture-suite"],
        "requirements": {item: milestone_id for item in requirement_ids},
        "milestones": {
            milestone_id: {
                "outcome": "The fixture behavior is implemented and independently verified",
                "status": "TODO",
                "review_cycles": 0,
                "review_override": None,
                "baseline": {"commit": "", "branch": "main"},
                "review_target": None,
                "as_built": {"artifact": None, "result": "PENDING"},
                "criteria": [
                    {
                        "id": f"{milestone_id}-AC{number}",
                        "status": "PENDING",
                        "text": text,
                        "evidence": [],
                    }
                    for number, text in enumerate(criteria, 1)
                ],
                "tasks": [],
                "reviews": [],
                "findings": [],
                "validation": [],
                "follow_ups": [],
                "external_jobs": [],
            }
        },
    }


def write_project(root: Path, scenario: str) -> tuple[dict, str]:
    milestone_id = "P2-M7c" if scenario == "namespaced-state" else "M1"
    requirement_ids = ["P2-R10.19"] if scenario == "namespaced-state" else ["FR1"]
    criteria = ["value() returns 2 and its test passes"]
    if scenario == "foreground-workers":
        requirement_ids = ["FR1", "FR2"]
        criteria = ["alpha() returns 2", "beta() returns 3"]
    elif scenario == "accuracy-regression":
        criteria = ["safe_join rejects paths that escape the configured root"]
    elif scenario == "high-risk-routing":
        criteria = ["the documented authorization boundary defaults to deny"]

    state = base_state(milestone_id, requirement_ids, criteria)
    harness = root / ".harness"
    harness.mkdir(parents=True)
    (harness / "reviews").mkdir()
    (harness / "evidence").mkdir()
    requirements = "# Requirements\n\n## Functional Requirements\n\n" + "".join(
        f"- [{item}] {text}\n" for item, text in zip(requirement_ids, criteria)
    ) + "\n## Constraints\n\n- Keep the change minimal.\n"
    (harness / "requirements.md").write_text(requirements)
    milestone = state["milestones"][milestone_id]
    boxes = "".join(f"- [ ] {item}\n" for item in criteria)
    (harness / "milestones.md").write_text(
        f"# Milestones\n\n## {milestone_id} — Fixture behavior\n\nStatus: TODO\n\n"
        f"### Outcome\n\n{milestone['outcome']}\n\n### Acceptance Criteria\n\n{boxes}\n"
        "### As-Built\n\nPENDING\n\n### Review Cycles\n\n0\n"
    )
    (harness / "state.json").write_text(json.dumps(state, indent=2) + "\n")

    if scenario == "foreground-workers":
        (root / "app.py").write_text("def alpha():\n    return 0\n\ndef beta():\n    return 0\n")
        (root / "test_app.py").write_text(
            "from app import alpha, beta\n\ndef test_alpha(): assert alpha() == 2\n"
            "def test_beta(): assert beta() == 3\n"
        )
    elif scenario == "accuracy-regression":
        (root / "app.py").write_text(
            "from pathlib import Path\n\ndef safe_join(root, value):\n"
            "    return Path(root) / value\n"
        )
        (root / "test_app.py").write_text(
            "from app import safe_join\n\n"
            "def test_escape_is_rejected(tmp_path):\n"
            "    try: safe_join(tmp_path, '../escape')\n"
            "    except ValueError: return\n"
            "    raise AssertionError('escape accepted')\n"
        )
    elif scenario == "high-risk-routing":
        (root / "SECURITY.md").write_text("# Authorization\n\nUndecided.\n")
        (root / "test_app.py").write_text(
            "from pathlib import Path\n\ndef test_default_deny_is_documented():\n"
            "    assert 'default deny' in Path('SECURITY.md').read_text().lower()\n"
        )
    else:
        (root / "app.py").write_text("def value():\n    return 1\n")
        (root / "test_app.py").write_text(
            "from app import value\n\ndef test_value(): assert value() == 2\n"
        )
    return state, milestone_id


def set_review_state(root: Path, state: dict, milestone_id: str, head: str, complete: bool) -> None:
    milestone = state["milestones"][milestone_id]
    milestone["status"] = "REVIEW"
    milestone["review_target"] = {"base": head, "head": head}
    (root / ".harness" / "milestones.md").write_text(
        (root / ".harness" / "milestones.md").read_text().replace("Status: TODO", "Status: REVIEW")
    )
    result_path = root / ".harness" / "reviews" / f"{milestone_id}-cycle1.result.json"
    if complete:
        result_path.write_text(json.dumps({
            "schema_version": 1,
            "milestone_id": milestone_id,
            "cycle": 1,
            "base": head,
            "head": head,
            "complete": True,
            "verdict": "PASS",
            "criteria": [
                {"id": item["id"], "status": "PASS", "evidence": ["pytest -q: pass"]}
                for item in milestone["criteria"]
            ],
            "findings": [],
            "scope": "SUBSTANTIVE",
            "tier": "Mid",
            "model": "sonnet",
            "effort": "medium",
            "reason_code": "STANDARD_REVIEW",
        }, indent=2) + "\n")
    else:
        (root / ".harness" / "reviews" / f"{milestone_id}-cycle1.md.partial.md").write_text(
            "Acceptance Criterion:\nvalue() returns 2\n\nTest Evidence:\npytest -q\n"
        )
    (root / ".harness" / "state.json").write_text(json.dumps(state, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario")
    args = parser.parse_args()
    root = Path.cwd()
    state, milestone_id = write_project(root, args.scenario)
    run("git", "init", "-b", "main")
    run("git", "config", "user.email", "eval@example.invalid")
    run("git", "config", "user.name", "Harness Eval")
    run("git", "add", ".")
    run("git", "commit", "-m", "fixture baseline")
    head = run("git", "rev-parse", "HEAD")
    state["milestones"][milestone_id]["baseline"]["commit"] = head

    if args.scenario == "review-before-terminal":
        set_review_state(root, state, milestone_id, head, complete=False)
    elif args.scenario == "review-after-terminal":
        # The implementation is correct at the reviewed HEAD. The durable result
        # is intentionally written after the response was notionally cut off.
        (root / "app.py").write_text("def value():\n    return 2\n")
        run("git", "add", "app.py")
        run("git", "commit", "-m", "implement fixture")
        head = run("git", "rev-parse", "HEAD")
        set_review_state(root, state, milestone_id, head, complete=True)
    elif args.scenario == "precredited-review":
        set_review_state(root, state, milestone_id, head, complete=False)
        for item in state["milestones"][milestone_id]["criteria"]:
            item["status"] = "PASS"
            item["evidence"] = ["unreviewed claim"]
        (root / ".harness" / "state.json").write_text(json.dumps(state, indent=2) + "\n")
    elif args.scenario == "external-job-resume":
        milestone = state["milestones"][milestone_id]
        milestone["status"] = "IN_PROGRESS"
        milestone["external_jobs"] = [{
            "id": "suite-1", "class": "fixture-suite", "owner": "orchestrator-v3",
            "started_at": "2026-01-01T00:00:00Z",
            "result_artifact": ".harness/evidence/suite-1.json", "status": "RUNNING",
        }]
        (root / ".harness" / "evidence" / "suite-1.json").write_text(json.dumps({
            "complete": True, "status": "COMPLETE", "summary": "fixture suite passed"
        }) + "\n")
        (root / ".harness" / "milestones.md").write_text(
            (root / ".harness" / "milestones.md").read_text().replace("Status: TODO", "Status: IN_PROGRESS")
        )
        (root / ".harness" / "state.json").write_text(json.dumps(state, indent=2) + "\n")
    else:
        (root / ".harness" / "state.json").write_text(json.dumps(state, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
