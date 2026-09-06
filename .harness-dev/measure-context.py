#!/usr/bin/env python3
"""Measure deduplicated token traffic and efficiency signals in Claude transcripts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import statistics
import subprocess


DEFAULT_PRICES = {
    "haiku": {"input": 0.80, "cache_creation": 1.00, "cache_read": 0.08, "output": 4.00},
    "sonnet": {"input": 3.00, "cache_creation": 3.75, "cache_read": 0.30, "output": 15.00},
    "opus": {"input": 15.00, "cache_creation": 18.75, "cache_read": 1.50, "output": 75.00},
}
ROLE_LIMITS = {"navigator": 10, "orchestrator": 30, "worker": 40,
               "verifier": 35, "reviewer": 50, "as-built": 30}
POLL_RE = re.compile(r"\b(sleep\s+\d+|while\b|until\b)")
CURL_RE = re.compile(r"(?m)(?:^|[;&|]\s*|\n\s*)curl(?:\s|$)")
CURL_TIMEOUT_RE = re.compile(
    r"(?:^|\s)(?:--max-time(?:=|\s+)|-m(?:=|\s*))"
    r"(?:\d+(?:\.\d+)?|\.\d+)(?=\s|$)"
)
VALIDATION_RE = re.compile(
    r"\b(pytest|unittest|npm\s+(?:run\s+)?test|pnpm\s+(?:run\s+)?test|"
    r"yarn\s+test|bun\s+test|cargo\s+test|go\s+test|rspec|vitest|jest|"
    r"tsc(?:\s+--noEmit)?|typecheck)\b", re.I
)
MILESTONE_RE = re.compile(r"\b(M\d+[a-z]?)\b", re.I)


def token_usage(usage):
    cache_creation = usage.get("cache_creation_input_tokens", 0)
    if isinstance(cache_creation, dict):
        cache_creation = sum(value for value in cache_creation.values() if isinstance(value, int))
    return {
        "input": usage.get("input_tokens", 0),
        "cache_creation": cache_creation,
        "cache_read": usage.get("cache_read_input_tokens", 0),
        "output": usage.get("output_tokens", 0),
    }


def turns(path):
    """Yield one row per API response, deduplicated by message id."""
    seen = {}
    with path.open() as transcript:
        for index, line in enumerate(transcript):
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") != "assistant":
                continue
            message = event.get("message") or {}
            message_id = message.get("id") or f"anonymous-{index}"
            row = seen.setdefault(
                message_id,
                {"usage": None, "tools": [], "timestamp": event.get("timestamp", ""),
                 "model": message.get("model", "")},
            )
            if message.get("usage") and row["usage"] is None:
                row["usage"] = message["usage"]
            for block in message.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    row["tools"].append(block)
    for row in seen.values():
        if row["usage"]:
            yield {
                "timestamp": row["timestamp"],
                "usage": token_usage(row["usage"]),
                "tools": row["tools"],
                "model": row["model"],
            }


def model_family(model):
    lowered = (model or "").lower()
    return next((family for family in DEFAULT_PRICES if family in lowered), "unknown")


def estimate_cost(usage, model, prices):
    rate = prices.get(model_family(model))
    if not rate:
        return None
    return sum(usage[key] * rate[key] / 1_000_000 for key in usage)


def milestone_from(*values):
    match = MILESTONE_RE.search(" ".join(str(value or "") for value in values))
    return match.group(1).upper() if match else "unknown"


def command_from(tool):
    if tool.get("name") not in {"Bash", "bash", "exec_command"}:
        return None
    arguments = tool.get("input") or {}
    return arguments.get("command") or arguments.get("cmd")


def normalise_command(command):
    return " ".join(command.strip().split())


def is_polling(command):
    if POLL_RE.search(command):
        return True
    return bool(CURL_RE.search(command)) and not bool(
        CURL_TIMEOUT_RE.search(command)
    )


def analyse(path, role, description, configured_model, milestone_override, prices):
    contexts, total_usage, tools, commands, model_counts = [], Counter(), Counter(), [], Counter()
    for turn in turns(path):
        usage = turn["usage"]
        total_usage.update(usage)
        contexts.append(sum(usage[key] for key in ("input", "cache_creation", "cache_read")))
        model = turn["model"] or configured_model
        model_counts[model] += 1
        for tool in turn["tools"]:
            tools[tool.get("name", "unknown")] += 1
            command = command_from(tool)
            if command:
                commands.append(normalise_command(command))
    if not contexts:
        return None
    model = model_counts.most_common(1)[0][0] if model_counts else configured_model
    usage = dict(total_usage)
    command_counts = Counter(commands)
    validation_counts = Counter(command for command in commands if VALIDATION_RE.search(command))
    poll_commands = [command for command in commands if is_polling(command)]
    return {
        "role": role,
        "milestone": milestone_override or milestone_from(description, path),
        "description": description,
        "model": model,
        "path": str(path),
        "api_turns": len(contexts),
        "peak_context": max(contexts),
        "median_context": int(statistics.median(contexts)),
        "tokens": usage,
        "token_traffic": sum(usage.values()),
        "estimated_cost_usd": estimate_cost(usage, model, prices),
        "tools": dict(tools),
        "polling_commands": poll_commands,
        "repeated_commands": {key: value for key, value in command_counts.items() if value > 1},
        "duplicate_validation_commands": {
            key: value - 1 for key, value in validation_counts.items() if value > 1
        },
        "review_diff_ranges": sorted({
            match.group(1) for command in commands
            for match in re.finditer(r"git\s+diff(?:\s+--[^ ]+)*\s+([^ ]+(?:\.\.|\.\.\.)[^ ]+)", command)
        }),
        "record_only_review": role == "reviewer" and "record_only" in description.lower(),
    }


def collect(session_dir, top_level_role, milestone, prices):
    directory = Path(session_dir).expanduser()
    rows = []
    subagents = directory / "subagents"
    if subagents.is_dir():
        metadata_by_stem = {
            path.name.removesuffix(".meta.json"): json.loads(path.read_text())
            for path in subagents.glob("*.meta.json")
        }
        for transcript in sorted(subagents.glob("*.jsonl")):
            metadata = metadata_by_stem.get(transcript.stem, {})
            role = metadata.get("agentType", "unknown").replace("harness:", "")
            row = analyse(transcript, role, metadata.get("description", ""),
                          metadata.get("model", ""), milestone, prices)
            if row:
                rows.append(row)
    top_transcript = directory.with_suffix(".jsonl")
    if top_transcript.exists():
        row = analyse(top_transcript, top_level_role, f"[{directory.name[:8]}]",
                      "", milestone, prices)
        if row:
            rows.append(row)
    return rows


def harness_identity(repository):
    plugin = repository / ".claude-plugin/plugin.json"
    version = json.loads(plugin.read_text()).get("version") if plugin.exists() else None
    completed = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        text=True, capture_output=True, check=False,
    )
    return {"version": version, "commit": completed.stdout.strip() if completed.returncode == 0 else None}


def aggregate(rows, harness):
    total = sum(row["token_traffic"] for row in rows)
    empty = lambda: {"contexts": 0, "api_turns": 0, "tokens": 0, "cost": 0.0}
    by_role, by_milestone = defaultdict(empty), defaultdict(empty)
    for row in rows:
        for bucket, key in ((by_role, row["role"]), (by_milestone, row["milestone"])):
            bucket[key]["contexts"] += 1
            bucket[key]["api_turns"] += row["api_turns"]
            bucket[key]["tokens"] += row["token_traffic"]
            bucket[key]["cost"] += row["estimated_cost_usd"] or 0
    parents = [row for row in rows if row["role"] in {"skill session", "parent", "controller"}]
    orchestrator_turns = [row["api_turns"] for row in rows if row["role"] == "orchestrator"]
    hard_limit_violations = [
        {"role": row["role"], "turns": row["api_turns"], "limit": ROLE_LIMITS[row["role"]], "path": row["path"]}
        for row in rows if row["role"] in ROLE_LIMITS and row["api_turns"] > ROLE_LIMITS[row["role"]]
    ]
    reviewer_rows = [row for row in rows if row["role"] == "reviewer"]
    return {
        "schema_version": 1,
        "harness": harness,
        "summary": {
            "contexts": len(rows),
            "api_turns": sum(row["api_turns"] for row in rows),
            "token_traffic": total,
            "estimated_cost_usd": sum(row["estimated_cost_usd"] or 0 for row in rows),
            "unpriced_contexts": sum(row["estimated_cost_usd"] is None for row in rows),
            "peak_context": max((row["peak_context"] for row in rows), default=0),
            "parent_share": sum(row["token_traffic"] for row in parents) / total if total else 0,
            "orchestrator_median_turns": statistics.median(orchestrator_turns) if orchestrator_turns else 0,
            "polling_violations": sum(len(row["polling_commands"]) for row in rows),
            "hard_limit_violations": hard_limit_violations,
            "workers_over_45_turns": sum(row["api_turns"] > 45 for row in rows if row["role"] == "worker"),
            "record_only_semantic_reviews": sum(row["record_only_review"] for row in reviewer_rows),
            "duplicate_validation_commands": sum(
                sum(row["duplicate_validation_commands"].values()) for row in rows
            ),
            "semantic_reviews": len(reviewer_rows),
            "semantic_review_diff_ranges": sum(len(row["review_diff_ranges"]) for row in reviewer_rows),
        },
        "by_role": dict(by_role),
        "by_milestone": dict(by_milestone),
        "contexts": rows,
    }


def print_report(report):
    print(f"{'role':<14}{'milestone':<10}{'model':<24}{'turns':>7}{'peak':>10}{'tokens':>14}{'cost':>10}")
    for row in sorted(report["contexts"], key=lambda value: -value["token_traffic"]):
        cost = "n/a" if row["estimated_cost_usd"] is None else f"${row['estimated_cost_usd']:.2f}"
        print(f"{row['role']:<14}{row['milestone']:<10}{row['model'][:23]:<24}"
              f"{row['api_turns']:>7}{row['peak_context']:>10,}{row['token_traffic']:>14,}{cost:>10}")
    summary = report["summary"]
    print(f"\nTOTAL {summary['api_turns']} turns, {summary['token_traffic']:,} tokens, "
          f"${summary['estimated_cost_usd']:.2f}")
    print(f"Peak context {summary['peak_context']:,}; parent share {summary['parent_share']:.1%}; "
          f"polling {summary['polling_violations']}; duplicate validation "
          f"{summary['duplicate_validation_commands']}")
    if summary["unpriced_contexts"]:
        print(f"WARNING: {summary['unpriced_contexts']} context(s) use an unpriced model; cost is partial")
    for role, values in sorted(report["by_role"].items(), key=lambda item: -item[1]["tokens"]):
        share = values["tokens"] / summary["token_traffic"] if summary["token_traffic"] else 0
        print(f"  {role:<14} n={values['contexts']:<3} turns={values['api_turns']:<5} "
              f"tokens={values['tokens']:>13,} share={share:>6.1%} cost=${values['cost']:.2f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_dirs", nargs="+")
    parser.add_argument("--top-level-role", default="skill session")
    parser.add_argument("--milestone", help="label every supplied session with this milestone")
    parser.add_argument("--prices", type=Path, help="JSON price map in USD per million tokens")
    parser.add_argument("--json", type=Path, dest="json_path", help="also write machine-readable report")
    parser.add_argument("--harness-repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    prices = json.loads(args.prices.read_text()) if args.prices else DEFAULT_PRICES
    rows = []
    for directory in args.session_dirs:
        rows.extend(collect(directory, args.top_level_role, args.milestone, prices))
    if not rows:
        parser.error("no assistant contexts found in the supplied session directories")
    report = aggregate(rows, harness_identity(args.harness_repo))
    print_report(report)
    if args.json_path:
        args.json_path.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
