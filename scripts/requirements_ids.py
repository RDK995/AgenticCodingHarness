"""Shared parsing for stable functional-requirement identifiers."""

from collections import Counter
import re


def functional_requirement_ids(text: str) -> tuple[set[str], list[str]]:
    """Return ids, synthesising FR<n> by bullet order for legacy documents."""
    section = re.search(
        r"(?ms)^## Functional Requirements\s*\n(.*?)(?=^## |\Z)", text
    )
    if not section:
        return set(), ["requirements document lacks a Functional Requirements section"]
    ids = []
    for number, item in enumerate(re.finditer(r"(?m)^\s*-\s+(.+)$", section.group(1)), 1):
        body = item.group(1).strip()
        explicit = re.match(
            r"(?:\[(FR\d+)\]|\*\*(FR\d+)\*\*|(FR\d+)\s*[:—-])",
            body,
            re.IGNORECASE,
        )
        ids.append(next(group for group in explicit.groups() if group).upper() if explicit else f"FR{number}")
    duplicates = sorted(requirement for requirement, count in Counter(ids).items() if count > 1)
    errors = ["requirements document repeats ids: " + ", ".join(duplicates)] if duplicates else []
    if not ids:
        errors.append("requirements document has no functional requirements")
    return set(ids), errors
