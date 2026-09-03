#!/usr/bin/env python3
"""Check a .harness/milestones.md ledger against its body.

Usage: check-ledger.py <path to milestones.md>
Exit 0 if the ledger matches the body, 1 otherwise. Prints every mismatch.
"""
import re
import sys

path = sys.argv[1]
lines = open(path).read().splitlines()

# --- body: every "## M<n> — " section, its Status: and its ### Review Cycles ---
body = {}          # id -> {"status":..., "cycles":..., "archived":bool}
order = []
cur = None
in_cycles = False
for ln in lines:
    m = re.match(r"^## (M[0-9a-z]+) — ", ln)
    if m:
        cur = m.group(1)
        order.append(cur)
        body[cur] = {"status": None, "cycles": None, "archived": False}
        in_cycles = False
        continue
    if cur is None:
        continue
    if ln.startswith("### "):
        in_cycles = ln.strip() == "### Review Cycles"
        continue
    if ln.startswith("Status:"):
        body[cur]["status"] = ln.split(":", 1)[1].strip()
    elif ln.startswith("Detail:"):
        body[cur]["archived"] = True
    elif in_cycles and ln.strip().isdigit() and body[cur]["cycles"] is None:
        body[cur]["cycles"] = ln.strip()

# --- ledger ---
try:
    start = lines.index("## Ledger")
except ValueError:
    print("FAIL: no '## Ledger' block")
    sys.exit(1)
if start > 3:
    print(f"FAIL: ledger is at line {start+1}, not the top of the file")

end = next((i for i in range(start + 1, len(lines))
            if lines[i].startswith("## ") and i != start), len(lines))
block = lines[start:end]

current = next((l.split(":", 1)[1].strip() for l in block if l.startswith("Current:")), None)
rows = {}
row_order = []
for l in block:
    if not l.startswith("|") or set(l) <= set("| -"):
        continue
    cells = [c.strip() for c in l.strip("|").split("|")]
    if cells[0] in ("id", ""):
        continue
    if len(cells) != 4:
        print(f"FAIL: row has {len(cells)} columns, expected 4: {l}")
        continue
    rows[cells[0]] = {"status": cells[1], "cycles": cells[2], "detail": cells[3]}
    row_order.append(cells[0])

ok = True


def fail(msg):
    global ok
    ok = False
    print("FAIL: " + msg)


if row_order != order:
    fail(f"ledger rows {row_order} do not match body sections {order}")

for mid in order:
    if mid not in rows:
        fail(f"{mid} has no ledger row")
        continue
    r, b = rows[mid], body[mid]
    if r["status"] != b["status"]:
        fail(f"{mid}: ledger status {r['status']!r} != body {b['status']!r}")
    if b["cycles"] is not None and r["cycles"] != b["cycles"]:
        fail(f"{mid}: ledger cycles {r['cycles']!r} != body {b['cycles']!r}")
    if b["archived"] and r["detail"] != "archived":
        fail(f"{mid}: body is archived, ledger detail says {r['detail']!r}")
    if not b["archived"] and r["detail"] != "here":
        fail(f"{mid}: body detail is here, ledger says {r['detail']!r}")

expected_current = next((m for m in order if body[m]["status"] != "DONE"), None)
expected = expected_current if expected_current else "none — all DONE"
if current != expected:
    fail(f"Current is {current!r}, expected {expected!r}")

if ok:
    print(f"OK: ledger matches body — {len(order)} milestone(s), Current: {current}")
sys.exit(0 if ok else 1)
