#!/usr/bin/env python3
"""Validate runtime-v3 paid-campaign authorization and completed result provenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


MINIMUM_VERSION = (2, 1, 269)
REQUIRED_CASES = {
    "01-namespaced-state", "07-evidence-routing",
    "08-high-risk-routing", "09-accuracy-regression",
}


def version(value: object) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", str(value or ""))
    return tuple(map(int, match.groups())) if match else None


def validate(manifest: dict, *, results: bool = False) -> list[str]:
    errors: list[str] = []
    campaign_id = manifest.get("campaign_id")
    authorization = manifest.get("authorization", {})
    maximum = authorization.get("max_cost_usd")
    if manifest.get("schema_version") != 1:
        errors.append("campaign schema_version must be 1")
    if not isinstance(campaign_id, str) or not re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", campaign_id
    ):
        errors.append("campaign_id must be a lowercase UUID")
    if not isinstance(maximum, (int, float)) or isinstance(maximum, bool) or maximum <= 0:
        errors.append("authorization.max_cost_usd must be positive")
    elif authorization.get("text") != (
        f"Authorize paid runtime-v3 campaign {campaign_id} up to ${maximum:g}"
    ):
        errors.append("authorization text does not exactly bind campaign id and maximum spend")

    harness = manifest.get("harness", {})
    target = manifest.get("target", {})
    runtime = manifest.get("runtime", {})
    protocol = manifest.get("protocol", {})
    for label, value in (
        ("harness.commit", harness.get("commit")),
        ("harness.version", harness.get("version")),
        ("target.fixture_commit", target.get("fixture_commit")),
        ("runtime.model", runtime.get("model")),
    ):
        if not isinstance(value, str) or not value or value.startswith("replace-"):
            errors.append(f"{label} must be pinned")
    observed = version(runtime.get("claude_code_version"))
    if observed is None or observed < MINIMUM_VERSION:
        errors.append("runtime.claude_code_version must be at least 2.1.269")
    if runtime.get("disable_background_tasks") is not True:
        errors.append("runtime must disable background tasks")
    if set(runtime.get("permissions", [])) != {"Bash", "Write", "Edit", "Agent", "Skill"}:
        errors.append("runtime permissions do not match the fixed campaign grant")
    if protocol.get("runs_per_arm") != 3:
        errors.append("protocol requires exactly 3 runs per arm")
    if protocol.get("arm_order") not in (["control", "treatment"], ["treatment", "control"]):
        errors.append("protocol arm_order must explicitly alternate the two arms")
    if protocol.get("ablation") != "none":
        errors.append("protocol ablation must be none for control/treatment runs")
    if set(protocol.get("cases", [])) != REQUIRED_CASES:
        errors.append("protocol cases do not match the fixed comparable set")

    arms = manifest.get("arms", {})
    if arms.get("control", {}).get("skill") != "implement":
        errors.append("control arm must use implement")
    if arms.get("treatment", {}).get("skill") != "implement-v3":
        errors.append("treatment arm must use implement-v3")
    if results:
        for arm in ("control", "treatment"):
            record = arms.get(arm, {})
            native_path = record.get("native_result")
            reports = record.get("measured_reports", [])
            if not isinstance(native_path, str) or not native_path:
                errors.append(f"{arm} arm lacks native_result")
            else:
                try:
                    native = json.loads(Path(native_path).read_text())
                except (OSError, json.JSONDecodeError) as error:
                    errors.append(f"{arm} native result cannot be read: {error}")
                else:
                    if native.get("schemaVersion") != 1 or native.get("partial") is True:
                        errors.append(f"{arm} native result is partial or has an unknown schema")
                    aggregates = native.get("aggregates", {})
                    if aggregates.get("casesPassed") != aggregates.get("casesTotal"):
                        errors.append(f"{arm} native eval cases did not all pass")
            if not isinstance(reports, list) or len(reports) < 3:
                errors.append(f"{arm} arm requires at least 3 measured reports")
            else:
                for report_path in reports:
                    if not Path(report_path).is_file():
                        errors.append(f"{arm} measured report is missing: {report_path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--results", action="store_true")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text())
    except (OSError, json.JSONDecodeError) as error:
        parser.error(f"cannot read campaign manifest: {error}")
    errors = validate(manifest, results=args.results)
    for error in errors:
        print(f"FAIL {error}")
    if not errors:
        print("PASS campaign manifest" + (" and results" if args.results else " preflight"))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
