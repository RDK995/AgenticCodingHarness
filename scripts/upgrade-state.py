#!/usr/bin/env python3
"""Explicitly upgrade an existing harness state file from schema v1 to v2."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


def upgrade(state: dict, attestation: str | None) -> dict:
    if state.get("schema_version") == 2:
        return deepcopy(state)
    if state.get("schema_version") != 1:
        raise ValueError("only schema_version 1 can be upgraded")
    result = deepcopy(state)
    result["schema_version"] = 2
    for milestone_id, milestone in result.get("milestones", {}).items():
        if not isinstance(milestone, dict):
            continue
        milestone.setdefault("external_jobs", [])
        if milestone.get("status") == "REVIEW" and any(
            isinstance(item, dict) and item.get("status") == "PASS"
            for item in milestone.get("criteria", [])
        ):
            raise ValueError(
                f"{milestone_id} is REVIEW with pre-credited PASS criteria; "
                "restore them to PENDING before upgrading"
            )
        if milestone.get("status") == "DONE":
            if not attestation:
                raise ValueError(
                    "completed legacy milestones require --attest-legacy-done; "
                    "the migration cannot invent historical terminal review evidence"
                )
            baseline = milestone.get("baseline") if isinstance(milestone.get("baseline"), dict) else {}
            head = baseline.get("commit") or "LEGACY_UNKNOWN_HEAD"
            milestone.setdefault("review_target", {"base": head, "head": head})
            milestone["legacy_completion"] = {
                "source": "explicit-migration-attestation",
                "attestation": attestation,
                "migrated_at": datetime.now(timezone.utc).isoformat(),
                "head": head,
            }
            as_built = milestone.get("as_built")
            if isinstance(as_built, dict) and as_built.get("result") in {None, "PENDING"}:
                as_built["result"] = "LEGACY_NOT_RECORDED"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--milestones", required=True, type=Path)
    parser.add_argument("--requirements", type=Path)
    parser.add_argument("--attest-legacy-done")
    args = parser.parse_args()
    try:
        original = args.state.read_text()
        state = json.loads(original)
        upgraded = upgrade(state, args.attest_legacy_done)
        if upgraded == state:
            print(f"OK: {args.state} is already schema v2")
            return 0
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = args.state.with_name(f"{args.state.name}.v1.{timestamp}.bak")
        backup.write_text(original)
        args.state.write_text(json.dumps(upgraded, indent=2) + "\n")
        command = [
            sys.executable,
            str(Path(__file__).with_name("check-state.py")),
            str(args.state),
            "--milestones",
            str(args.milestones),
        ]
        if args.requirements:
            command.extend(["--requirements", str(args.requirements)])
        checked = subprocess.run(command, text=True, capture_output=True, check=False)
        if checked.returncode:
            args.state.write_text(original)
            backup.unlink(missing_ok=True)
            raise ValueError("upgraded state failed validation: " + checked.stderr.strip())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: upgraded {args.state} to schema v2; backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
