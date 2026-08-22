#!/usr/bin/env python3
"""Measure a harness run's context cost from its Claude Code transcript.

Method used for the §48 baseline. Point it at one or more session directories:

    ./measure-context.py ~/.claude/projects/<project>/<session-uuid> [more...]
    ./measure-context.py --top-level-role orchestrator <dir> [more...]

Since §48 a milestone runs as several invocations, so it spans several sessions;
pass them all and the totals aggregate. `--top-level-role` labels each session's
own transcript, which is the orchestrator when invoked with
`--agent harness:orchestrator` and the skill session when invoked with
`/harness:implement` (the default).

It reads <session-uuid>.jsonl and <session-uuid>/subagents/*.jsonl, counting
input + cache_creation + cache_read + output tokens per assistant turn.
`fixed` is the smallest context observed times the turn count; `growth` is the
rest. Reports per-context totals, each orchestrator's turn profile, and the split
between the implementation phase and the review/fix phase.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path


def turns(path):
    for line in path.open():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") != "assistant":
            continue
        u = (d.get("message") or {}).get("usage") or {}
        if not u:
            continue
        ctx = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
               + u.get("cache_read_input_tokens", 0))
        content = (d.get("message") or {}).get("content") or []
        tools = [b for b in content
                 if isinstance(b, dict) and b.get("type") == "tool_use"]
        yield d.get("timestamp", ""), ctx, u.get("output_tokens", 0), tools


def analyse(path):
    ctxs, total, tools, ts = [], 0, Counter(), []
    for t, ctx, out, tu in turns(path):
        ctxs.append(ctx)
        total += ctx + out
        ts.append(t)
        for b in tu:
            tools[b["name"]] += 1
    if not ctxs:
        return None
    base = min(ctxs)
    ctxs.sort()
    return dict(turns=len(ctxs), total=total, base=base, peak=ctxs[-1],
                median=ctxs[len(ctxs) // 2], growth=total - base * len(ctxs),
                tools=tools, first=ts[0], last=ts[-1])


def orchestrator_profile(path):
    notool = reads_out = reads_repo = poll = 0
    bash = Counter()
    rows = []
    first_review = None
    for t, ctx, out, tu in turns(path):
        rows.append((t, ctx + out))
        if not tu:
            notool += 1
        for b in tu:
            name, i = b["name"], b.get("input", {})
            if name == "Read":
                p = i.get("file_path", "")
                if "/tasks/" in p and p.endswith(".output"):
                    reads_out += 1
                else:
                    reads_repo += 1
            elif name == "Bash":
                c = i.get("command", "")
                if re.search(r"\b(until|while)\b.*\bls\b|sleep \d", c):
                    bash["wait/poll"] += 1
                    poll += 1
                elif re.search(r"bun (test|x tsc)|pytest|npm test|tsc --noEmit", c):
                    bash["run tests/typecheck"] += 1
                elif re.search(r"git (diff|show|log|status)", c):
                    bash["git inspect"] += 1
                elif re.search(r"\b(grep|rg)\b", c):
                    bash["grep"] += 1
                elif re.search(r"\b(sed -n|cat|head|tail)\b", c):
                    bash["read file via bash"] += 1
                else:
                    bash["other"] += 1
            elif name in ("Agent", "Task"):
                d = str(i.get("description", "")) + str(i.get("subagent_type", ""))
                if "review" in d.lower() and first_review is None:
                    first_review = t
    n = len(rows)
    print(f"  tool-free turns      {notool}/{n} ({100 * notool / n:.0f}%)")
    print(f"  Read .output files   {reads_out}")
    print(f"  Read repo files      {reads_repo}")
    print(f"  poll/sleep calls     {poll}")
    print(f"  bash                 {dict(bash.most_common())}")
    if first_review:
        pre = sum(c for t, c in rows if t < first_review)
        post = sum(c for t, c in rows if t >= first_review)
        npre = sum(1 for t, _ in rows if t < first_review)
        print(f"  plan+implement       {npre} turns, {pre:,} tokens "
              f"({100 * pre / (pre + post):.0f}%)")
        print(f"  review/fix           {n - npre} turns, {post:,} tokens "
              f"({100 * post / (pre + post):.0f}%)")


def collect(session_dir, top_level_role):
    d = Path(session_dir).expanduser()
    rows = []
    subagents = d / "subagents"
    if subagents.is_dir():
        for meta in sorted(subagents.glob("*.meta.json")):
            m = json.loads(meta.read_text())
            jsonl = meta.with_suffix("").with_suffix(".jsonl")
            a = analyse(jsonl)
            if not a:
                continue
            a.update(kind=m.get("agentType", "?").replace("harness:", ""),
                     desc=m.get("description", ""),
                     model=m.get("model", "(default)"), path=jsonl)
            rows.append(a)
    top = d.with_suffix(".jsonl")
    main_a = analyse(top)
    if main_a:
        main_a.update(kind=top_level_role, desc=f"[{d.name[:8]}]",
                      model="", path=top)
        rows.append(main_a)
    return rows


def main(session_dirs, top_level_role):
    rows = []
    for sd in session_dirs:
        rows += collect(sd, top_level_role)

    print(f"{'kind':<14}{'model':<12}{'description':<40}"
          f"{'turns':>6}{'peak':>9}{'median':>9}{'tokens':>13}{'growth':>8}")
    for r in sorted(rows, key=lambda x: -x["total"]):
        g = 100 * r["growth"] / r["total"]
        print(f"{r['kind']:<14}{r['model']:<12}{r['desc'][:39]:<40}"
              f"{r['turns']:>6}{r['peak']:>9,}{r['median']:>9,}"
              f"{r['total']:>13,}{g:>7.0f}%")

    grand = sum(r["total"] for r in rows)
    print(f"\nTOTAL {sum(r['turns'] for r in rows)} turns, {grand:,} tokens")
    for kind in ("orchestrator", "worker", "verifier", "reviewer",
                 "skill session"):
        s = [r for r in rows if r["kind"] == kind]
        if not s:
            continue
        tok = sum(r["total"] for r in s)
        print(f"  {kind:<14} n={len(s):<3} turns={sum(r['turns'] for r in s):<6}"
              f"tokens={tok:>13,}  {100 * tok / grand:>5.1f}%")

    for r in rows:
        if r["kind"] == "orchestrator":
            print(f"\norchestrator — {r['desc']}")
            orchestrator_profile(r["path"])


if __name__ == "__main__":
    args = sys.argv[1:]
    role = "skill session"
    if "--top-level-role" in args:
        i = args.index("--top-level-role")
        role = args[i + 1]
        del args[i:i + 2]
    if not args:
        sys.exit(__doc__)
    main(args, role)
