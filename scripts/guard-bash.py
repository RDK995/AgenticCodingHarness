#!/usr/bin/env python3
"""Deny open-ended waiting from Bash tool calls made under the harness plugin."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile


SHELL_SLEEP = re.compile(r"(?im)(?:^|[;&|]\s*|\n\s*)sleep(?:\s|$)")
SHELL_POLL_LOOP = re.compile(r"(?im)(?:^|[;&|]\s*|\n\s*)(?:until|while)\b")
CURL = re.compile(r"(?m)(?:^|[;&|]\s*|\n\s*)curl(?:\s|$)")
CURL_TIMEOUT = re.compile(
    r"(?:^|\s)(?:--max-time(?:=|\s+)|-m(?:=|\s*))"
    r"(?:\d+(?:\.\d+)?|\.\d+)(?=\s|$)"
)
READINESS = re.compile(
    r"(?i)(?:/health(?:z)?\b|/ready\b|\bready(?:ness)?\b|"
    r"(?:^|[;&|]\s*|\n\s*)(?:pgrep|lsof)\b|"
    r"(?:^|[;&|]\s*|\n\s*)test\s+-(?:e|f|S)\b)"
)


def response(decision: str, reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }


def deny(reason: str) -> dict:
    return response("deny", reason)


def allow() -> dict:
    return response("allow", "Harness wait guard passed.")


def state_file(payload: dict) -> Path:
    root = Path(
        os.environ.get(
            "HARNESS_GUARD_STATE_DIR",
            str(Path(tempfile.gettempdir()) / "claude-harness-wait-guard"),
        )
    )
    identity = "\0".join(
        str(payload.get(field, "top-level"))
        for field in ("session_id", "agent_id", "agent_type")
    )
    name = hashlib.sha256(identity.encode()).hexdigest() + ".json"
    return root / name


def repeated_readiness_check(payload: dict, command: str) -> bool:
    """Return true on the second consecutive identical readiness check."""
    path = state_file(payload)
    digest = hashlib.sha256(" ".join(command.split()).encode()).hexdigest()
    try:
        previous = json.loads(path.read_text()) if path.exists() else {}
        if previous.get("digest") == digest:
            return True
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"digest": digest}) + "\n")
        temporary.replace(path)
    except (OSError, ValueError):
        # The hard bans still apply. Failure to retain this optional second-line
        # defence must not make every otherwise-safe Bash command unusable.
        return False
    return False


def evaluate(payload: dict) -> dict:
    if payload.get("tool_name") != "Bash":
        return allow()

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict) or not isinstance(tool_input.get("command"), str):
        return deny("Harness wait guard could not identify the Bash command; refusing it safely.")

    command = tool_input["command"]
    if SHELL_SLEEP.search(command):
        return deny(
            "Harness policy forbids foreground sleep. Run one readiness check with "
            "an explicit timeout, then return the observed state."
        )
    if SHELL_POLL_LOOP.search(command):
        return deny(
            "Harness policy forbids shell while/until polling. Run one bounded "
            "readiness check, then return instead of polling."
        )
    if CURL.search(command) and not CURL_TIMEOUT.search(command):
        return deny(
            "Harness network commands require an explicit timeout (for curl, "
            "use --max-time)."
        )
    if READINESS.search(command) and repeated_readiness_check(payload, command):
        return deny(
            "This agent already ran the identical readiness check. Return the "
            "state observed instead of polling again."
        )
    return allow()


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("hook input is not an object")
        result = evaluate(payload)
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        result = deny("Harness wait guard received malformed input; refusing the tool call safely.")
    sys.stdout.write(json.dumps(result, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
