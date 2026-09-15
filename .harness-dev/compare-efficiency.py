#!/usr/bin/env python3
"""Compare complete control and treatment efficiency reports fail-closed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics


MIN_RUNS_PER_ARM = 3


def load_reports(paths: list[Path], expected_arm: str) -> tuple[list[dict], list[str]]:
    reports: list[dict] = []
    errors: list[str] = []
    run_ids: set[str] = set()
    for path in paths:
        try:
            report = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{path}: cannot read report: {error}")
            continue
        manifest = report.get("manifest", {})
        summary = report.get("summary", {})
        run_id = manifest.get("run_id")
        if report.get("schema_version") != 2:
            errors.append(f"{path}: report schema_version must be 2")
        if manifest.get("arm") != expected_arm:
            errors.append(f"{path}: expected {expected_arm} arm, got {manifest.get('arm')!r}")
        if manifest.get("comparable") is not True:
            errors.append(f"{path}: report is not marked comparable")
        if not isinstance(run_id, str) or not run_id:
            errors.append(f"{path}: missing run_id")
        elif run_id in run_ids:
            errors.append(f"{path}: duplicate run_id {run_id}")
        else:
            run_ids.add(run_id)
        for field in ("cost_per_accepted_unit_usd", "tokens_per_accepted_unit"):
            value = summary.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                errors.append(f"{path}: {field} must be positive")
        if summary.get("accepted_units", 0) <= 0:
            errors.append(f"{path}: accepted_units must be positive")
        retry_rate = summary.get("retry_rate")
        if not isinstance(retry_rate, (int, float)) or isinstance(retry_rate, bool) or retry_rate < 0:
            errors.append(f"{path}: retry_rate must be a non-negative number")
        accuracy = report.get("accuracy", {})
        if accuracy.get("passed") is not True:
            errors.append(f"{path}: accuracy.passed must be true")
        reports.append(report)
    if len(reports) < MIN_RUNS_PER_ARM:
        errors.append(
            f"{expected_arm}: requires at least {MIN_RUNS_PER_ARM} complete reports, got {len(reports)}"
        )
    return reports, errors


def values(reports: list[dict], field: str) -> list[float]:
    return [float(report["summary"][field]) for report in reports]


def compare(control: list[dict], treatment: list[dict]) -> dict:
    control_cost = values(control, "cost_per_accepted_unit_usd")
    treatment_cost = values(treatment, "cost_per_accepted_unit_usd")
    control_tokens = values(control, "tokens_per_accepted_unit")
    treatment_tokens = values(treatment, "tokens_per_accepted_unit")
    control_retries = values(control, "retry_rate")
    treatment_retries = values(treatment, "retry_rate")

    metrics = {
        "control_median_cost": statistics.median(control_cost),
        "treatment_median_cost": statistics.median(treatment_cost),
        "control_median_tokens": statistics.median(control_tokens),
        "treatment_median_tokens": statistics.median(treatment_tokens),
        "control_worst_cost": max(control_cost),
        "treatment_worst_cost": max(treatment_cost),
        "control_median_retry_rate": statistics.median(control_retries),
        "treatment_median_retry_rate": statistics.median(treatment_retries),
    }
    metrics["cost_reduction"] = 1 - (
        metrics["treatment_median_cost"] / metrics["control_median_cost"]
    )
    gates = {
        "accuracy passes in every run": all(
            report.get("accuracy", {}).get("passed") is True
            for report in [*control, *treatment]
        ),
        "median accepted-task cost improves by at least 20%": metrics["cost_reduction"] >= 0.20,
        "median accepted-task tokens improve": (
            metrics["treatment_median_tokens"] < metrics["control_median_tokens"]
        ),
        "treatment worst cost is within 10% of control": (
            metrics["treatment_worst_cost"] <= metrics["control_worst_cost"] * 1.10
        ),
        "median retry rate is no worse": (
            metrics["treatment_median_retry_rate"] <= metrics["control_median_retry_rate"]
        ),
    }
    return {"schema_version": 1, "metrics": metrics, "gates": gates, "passed": all(gates.values())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", nargs="+", required=True, type=Path)
    parser.add_argument("--treatment", nargs="+", required=True, type=Path)
    parser.add_argument("--json", type=Path, dest="json_path")
    args = parser.parse_args()

    control, control_errors = load_reports(args.control, "control")
    treatment, treatment_errors = load_reports(args.treatment, "treatment")
    errors = [*control_errors, *treatment_errors]
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1

    result = compare(control, treatment)
    for name, passed in result["gates"].items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    print(f"Cost reduction: {result['metrics']['cost_reduction']:.1%}")
    if args.json_path:
        args.json_path.write_text(json.dumps(result, indent=2) + "\n")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
