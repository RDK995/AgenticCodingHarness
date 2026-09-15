"""Validation helpers for compact, terminal milestone-review results."""

from __future__ import annotations

import json
from pathlib import Path
import re


VERDICTS = {"PASS", "CHANGES_REQUIRED", "BLOCKED"}
CRITERION_RESULTS = {"PASS", "FAIL"}
SEVERITIES = {"BLOCKER", "IMPORTANT", "OPTIONAL"}
FINDING_STATUSES = {"OPEN", "RESOLVED"}
SCOPES = {"SUBSTANTIVE", "RECORD_ONLY"}


def load_result(path: Path) -> dict:
    try:
        result = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read valid review-result JSON from {path}: {error}") from error
    if not isinstance(result, dict):
        raise ValueError("review-result root must be an object")
    return result


def validate_result(
    result: dict,
    *,
    milestone_id: str | None = None,
    head: str | None = None,
    criterion_ids: set[str] | None = None,
) -> list[str]:
    """Return every reason a purported terminal review result is unsafe to use."""
    errors: list[str] = []
    if result.get("schema_version") != 1:
        errors.append("review result schema_version must be 1")
    if result.get("complete") is not True:
        errors.append("review result is not terminal: complete must be true")

    actual_milestone = result.get("milestone_id")
    if not isinstance(actual_milestone, str) or not actual_milestone:
        errors.append("review result milestone_id must be a non-empty string")
    elif milestone_id is not None and actual_milestone != milestone_id:
        errors.append(
            f"review result milestone mismatch: expected {milestone_id}, got {actual_milestone}"
        )

    cycle = result.get("cycle")
    if not isinstance(cycle, int) or isinstance(cycle, bool) or cycle < 1:
        errors.append("review result cycle must be a positive integer")

    for field in ("base", "head"):
        if not isinstance(result.get(field), str) or not result.get(field):
            errors.append(f"review result {field} must be a non-empty commit id")
    if head is not None and result.get("head") != head:
        errors.append(
            f"review result HEAD mismatch: expected {head}, got {result.get('head')!r}"
        )

    verdict = result.get("verdict")
    if verdict not in VERDICTS:
        errors.append(f"review result verdict is invalid: {verdict!r}")
    scope = result.get("scope")
    if scope not in SCOPES:
        errors.append(f"review result scope is invalid: {scope!r}")
    elif scope == "RECORD_ONLY" and verdict != "CHANGES_REQUIRED":
        errors.append("RECORD_ONLY scope is valid only for CHANGES_REQUIRED")

    report_artifact = result.get("report_artifact")
    if verdict == "CHANGES_REQUIRED":
        if (
            not isinstance(report_artifact, str)
            or not re.fullmatch(r"\.harness/reviews/[^/]+\.md", report_artifact)
        ):
            errors.append(
                "CHANGES_REQUIRED review result requires a .harness/reviews/*.md report_artifact"
            )
    elif report_artifact is not None:
        errors.append("report_artifact must be omitted unless verdict is CHANGES_REQUIRED")

    criteria = result.get("criteria")
    actual_ids: list[str] = []
    statuses: list[str] = []
    if not isinstance(criteria, list) or not criteria:
        errors.append("review result criteria must be a non-empty array")
    else:
        for index, criterion in enumerate(criteria):
            prefix = f"review result criteria[{index}]"
            if not isinstance(criterion, dict):
                errors.append(f"{prefix} must be an object")
                continue
            criterion_id = criterion.get("id")
            if not isinstance(criterion_id, str) or not criterion_id:
                errors.append(f"{prefix}.id must be a non-empty string")
            else:
                actual_ids.append(criterion_id)
            status = criterion.get("status")
            if status not in CRITERION_RESULTS:
                errors.append(f"{prefix}.status is invalid: {status!r}")
            else:
                statuses.append(status)
            evidence = criterion.get("evidence")
            if not isinstance(evidence, list) or not evidence or not all(
                isinstance(item, str) and item.strip() for item in evidence
            ):
                errors.append(f"{prefix}.evidence must contain at least one non-empty string")

    duplicates = sorted({item for item in actual_ids if actual_ids.count(item) > 1})
    if duplicates:
        errors.append("review result repeats criterion ids: " + ", ".join(duplicates))
    if criterion_ids is not None:
        actual_set = set(actual_ids)
        missing = sorted(criterion_ids - actual_set)
        extra = sorted(actual_set - criterion_ids)
        if missing:
            errors.append("review result is missing criteria: " + ", ".join(missing))
        if extra:
            errors.append("review result has unknown criteria: " + ", ".join(extra))

    findings = result.get("findings")
    open_blocking = []
    finding_ids: list[str] = []
    if not isinstance(findings, list):
        errors.append("review result findings must be an array")
    else:
        for index, finding in enumerate(findings):
            prefix = f"review result findings[{index}]"
            if not isinstance(finding, dict):
                errors.append(f"{prefix} must be an object")
                continue
            finding_id = finding.get("id")
            if not isinstance(finding_id, str) or not finding_id:
                errors.append(f"{prefix}.id must be a non-empty string")
            else:
                finding_ids.append(finding_id)
            if finding.get("severity") not in SEVERITIES:
                errors.append(f"{prefix}.severity is invalid: {finding.get('severity')!r}")
            if finding.get("status") not in FINDING_STATUSES:
                errors.append(f"{prefix}.status is invalid: {finding.get('status')!r}")
            if not isinstance(finding.get("summary"), str) or not finding.get("summary"):
                errors.append(f"{prefix}.summary must be a non-empty string")
            if (
                finding.get("severity") in {"BLOCKER", "IMPORTANT"}
                and finding.get("status") == "OPEN"
            ):
                open_blocking.append(finding_id or f"index {index}")
    duplicate_findings = sorted(
        {item for item in finding_ids if finding_ids.count(item) > 1}
    )
    if duplicate_findings:
        errors.append("review result repeats finding ids: " + ", ".join(duplicate_findings))

    if verdict == "PASS":
        if any(status != "PASS" for status in statuses) or len(statuses) != len(actual_ids):
            errors.append("PASS review result requires every criterion to PASS")
        if open_blocking:
            errors.append(
                "PASS review result has open blocking findings: " + ", ".join(open_blocking)
            )
    elif verdict == "CHANGES_REQUIRED":
        if statuses and all(status == "PASS" for status in statuses) and not open_blocking:
            errors.append(
                "CHANGES_REQUIRED review result requires a failed criterion or open blocking finding"
            )
    elif verdict == "BLOCKED":
        if not isinstance(result.get("blocked_reason"), str) or not result.get("blocked_reason"):
            errors.append("BLOCKED review result requires blocked_reason")

    for field in ("tier", "model", "effort", "reason_code"):
        if not isinstance(result.get(field), str) or not result.get(field):
            errors.append(f"review result {field} must be a non-empty string")
    return errors


def criterion_statuses(result: dict) -> dict[str, str]:
    return {item["id"]: item["status"] for item in result["criteria"]}
