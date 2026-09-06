#!/usr/bin/env python3
"""Apply the token-efficiency release gates to one or more measured field runs."""

import argparse
import json
from pathlib import Path


EXPECTED_ROLES = {"orchestrator", "worker", "verifier", "reviewer"}
CONTROLLER_ROLES = {"skill session", "parent", "controller"}


def check(report, accuracy):
    summary = report["summary"]
    observed_roles = set(report.get("by_role", {}))
    gates = {
        "at least one context was measured": summary.get("contexts", 0) > 0,
        "measured traffic and API turns are nonzero": (
            summary.get("api_turns", 0) > 0 and summary.get("token_traffic", 0) > 0
        ),
        "all expected execution roles are present": EXPECTED_ROLES <= observed_roles,
        "a parent/controller context is present": bool(CONTROLLER_ROLES & observed_roles),
        "zero foreground polling": summary["polling_violations"] == 0,
        "zero hard-limit violations": not summary["hard_limit_violations"],
        "orchestrator median no higher than 22 turns": summary["orchestrator_median_turns"] <= 22,
        "no worker over 45 turns": summary["workers_over_45_turns"] == 0,
        "no record-only semantic review": summary["record_only_semantic_reviews"] == 0,
        "parent traffic no more than 15%": summary["parent_share"] <= 0.15,
        "behavioural fixtures pass": accuracy.get("behavioural_fixtures_pass") is True,
        "production changes independently verified": accuracy.get("independent_verification") is True,
        "milestones independently reviewed": accuracy.get("independent_milestone_review") is True,
    }
    return gates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--accuracy-evidence", required=True, type=Path)
    args = parser.parse_args()
    accuracy = json.loads(args.accuracy_evidence.read_text())
    failed = False
    for path in args.reports:
        report = json.loads(path.read_text())
        print(f"{path}: harness {report['harness'].get('version')} {report['harness'].get('commit')}")
        for name, passed in check(report, accuracy).items():
            print(f"  {'PASS' if passed else 'FAIL'} {name}")
            failed = failed or not passed
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
