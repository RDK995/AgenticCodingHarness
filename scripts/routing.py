"""Canonical v3 task-routing reason codes and model/effort expectations."""

ROUTES = {
    "MECHANICAL_WITH_ORACLE": {"tier": "Cheap", "model": "haiku", "effort": "low"},
    "STANDARD_IMPLEMENTATION": {"tier": "Mid", "model": "sonnet", "effort": "medium"},
    "EVIDENCE_SYNTHESIS": {"tier": "Mid", "model": "sonnet", "effort": "medium"},
    "JUDGMENT_NO_ORACLE": {"tier": "Top", "model": "opus", "effort": "high"},
    "ESCALATED_AFTER_FAILED_ORACLE": {"tier": "Top", "model": "opus", "effort": "high"},
}


def validate_routing(routing: dict) -> list[str]:
    reason = routing.get("reason_code")
    expected = ROUTES.get(reason)
    if not expected:
        return [f"unknown routing reason_code {reason!r}"]
    errors = []
    if routing.get("tier") != expected["tier"]:
        errors.append(
            f"{reason} requires tier {expected['tier']}, got {routing.get('tier')!r}"
        )
    model = str(routing.get("model", "")).lower()
    if expected["model"] not in model:
        errors.append(
            f"{reason} requires a {expected['model']} model, got {routing.get('model')!r}"
        )
    if routing.get("effort") != expected["effort"]:
        errors.append(
            f"{reason} requires effort {expected['effort']}, got {routing.get('effort')!r}"
        )
    if expected["tier"] == "Top" and not routing.get("detail"):
        errors.append(f"{reason} requires a named risk detail")
    return errors
