#!/usr/bin/env python3
"""Validate a compact terminal review result, optionally against harness state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_result import load_result, validate_result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--milestone")
    parser.add_argument("--head")
    args = parser.parse_args()

    expected_ids = None
    milestone_id = args.milestone
    try:
        result = load_result(args.result)
        if args.state:
            state = json.loads(args.state.read_text())
            milestone_id = milestone_id or result.get("milestone_id")
            milestone = state.get("milestones", {}).get(milestone_id)
            if not isinstance(milestone, dict):
                raise ValueError(f"milestone {milestone_id!r} is absent from state")
            expected_ids = {
                item.get("id")
                for item in milestone.get("criteria", [])
                if isinstance(item, dict) and item.get("id")
            }
        errors = validate_result(
            result,
            milestone_id=milestone_id,
            head=args.head,
            criterion_ids=expected_ids,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        errors = [str(error)]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"OK: terminal {result['verdict']} review for "
        f"{result['milestone_id']} at {result['head']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
