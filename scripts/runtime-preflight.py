#!/usr/bin/env python3
"""Fail-closed static and live-evidence checks for the v3 harness runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


MINIMUM_VERSION = (2, 1, 269)


def parse_version(text: str | None) -> tuple[int, int, int] | None:
    if not text:
        return None
    match = re.search(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)", text)
    return tuple(map(int, match.groups())) if match else None


def claude_version() -> str | None:
    completed = subprocess.run(
        ["claude", "--version"], text=True, capture_output=True, check=False
    )
    if completed.returncode:
        return None
    return (completed.stdout or completed.stderr).strip().splitlines()[0]


def static_checks(plugin_root: Path, version_text: str | None) -> dict[str, bool]:
    manifest = plugin_root / ".claude-plugin" / "plugin.json"
    hooks = plugin_root / "hooks" / "hooks.json"
    guard = plugin_root / "scripts" / "guard-bash.py"
    try:
        hook_data = json.loads(hooks.read_text())
    except (OSError, json.JSONDecodeError):
        hook_data = {}
    command = json.dumps(hook_data)
    version = parse_version(version_text)
    return {
        "supported Claude Code version": version is not None and version >= MINIMUM_VERSION,
        "plugin manifest exists": manifest.is_file(),
        "PreToolUse Bash hook is registered": (
            hooks.is_file() and "PreToolUse" in command and '"Bash"' in command
        ),
        "hook invokes the repository guard": "scripts/guard-bash.py" in command,
        "guard implementation exists": guard.is_file(),
        "v3 launcher exists": (plugin_root / "scripts" / "run-harness-v3.py").is_file(),
        "v3 controller and skill exist": (
            (plugin_root / "agents" / "controller.md").is_file()
            and (plugin_root / "skills" / "implement-v3" / "SKILL.md").is_file()
        ),
    }


def live_checks(evidence: dict, plugin_root: Path, audit_events: list[dict]) -> dict[str, bool]:
    parent = evidence.get("hook_probes", {}).get("parent", {})
    child = evidence.get("hook_probes", {}).get("child", {})
    foreground = evidence.get("foreground", {})
    audited_agents = {event.get("agent_type") for event in audit_events}
    denied_rules = {event.get("rule_id") for event in audit_events if event.get("decision") == "deny"}
    return {
        "live evidence is terminal": evidence.get("complete") is True,
        "live plugin root matches checkout": (
            Path(evidence.get("plugin_root", "/missing")).resolve() == plugin_root.resolve()
        ),
        "parent hook allows safe and bounded commands": (
            parent.get("safe_allowed") is True and parent.get("bounded_curl_allowed") is True
        ),
        "parent hook denies polling": parent.get("sleep_denied") is True,
        "child hook allows safe and bounded commands": (
            child.get("safe_allowed") is True and child.get("bounded_curl_allowed") is True
        ),
        "child hook denies polling": child.get("sleep_denied") is True,
        "parent and child decisions are audited": (
            {"top-level", "harness:worker"} <= audited_agents
            and "FOREGROUND_SLEEP" in denied_rules
        ),
        "two foreground agents returned": (
            foreground.get("dispatched") == 2 and foreground.get("returned") == 2
        ),
        "foreground results returned in initiating turn": (
            foreground.get("initiating_turn") is True
        ),
        "zero notification re-entry in probe": foreground.get("notification_re_entries") == 0,
        "zero polling in probe": foreground.get("polling_violations") == 0,
    }


def read_audit(path: Path) -> list[dict]:
    events = []
    for line in path.read_text().splitlines():
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("audit log contains a non-object event")
        events.append(value)
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--claude-version", help="override version discovery for deterministic tests")
    parser.add_argument("--live-evidence", type=Path)
    parser.add_argument("--audit-log", type=Path)
    args = parser.parse_args()
    version_text = args.claude_version or claude_version()
    checks = static_checks(args.plugin_root, version_text)
    if args.live_evidence or args.audit_log:
        if not args.live_evidence or not args.audit_log:
            parser.error("--live-evidence and --audit-log must be supplied together")
        try:
            evidence = json.loads(args.live_evidence.read_text())
            audit_events = read_audit(args.audit_log)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            parser.error(f"cannot read live preflight evidence: {error}")
        checks.update(live_checks(evidence, args.plugin_root, audit_events))
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if not checks["supported Claude Code version"]:
        print(
            "Required: Claude Code >= " + ".".join(map(str, MINIMUM_VERSION))
            + f"; observed: {version_text or 'unavailable'}",
            file=sys.stderr,
        )
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
