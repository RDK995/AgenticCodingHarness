#!/usr/bin/env bash
# M7-T2: read-only evidence gatherer for M7-AC1 (a milestone reached DONE with branch commits)
# and M7-AC2 (start, finish and stop notifications each sent through ntfy with HTTP 200).
# Reads the fixture only. Writes nothing, makes no network calls, changes no git state.
set -u

FIX=/Users/ryankenny/Tools/harness-m7-fixture
STATE="$FIX/.harness/state.json"
LOOP="$FIX/.harness/loop/loop.log"
BRANCH=m1-divide

echo "== 1. fixture milestone statuses ($STATE)"
statuses=$(python3 -I - "$STATE" <<'PY'
import json, sys
milestones = json.load(open(sys.argv[1], encoding="utf-8")).get("milestones", {})
for identifier, record in milestones.items():
    print(f"{identifier} {record.get('status')}")
PY
)
printf '%s\n' "$statuses"
done_count=$(printf '%s\n' "$statuses" | grep -c ' DONE$')

echo
echo "== 2. git log main..$BRANCH (fixture)"
commits=$(git --no-optional-locks -C "$FIX" log --oneline "main..$BRANCH" 2>&1)
printf '%s\n' "$commits"
commit_count=$(git --no-optional-locks -C "$FIX" log --oneline "main..$BRANCH" 2>/dev/null | grep -c .)

echo
echo "== 2b. git branch --list (fixture)"
git --no-optional-locks -C "$FIX" branch --list 2>&1

echo
echo "== 3. loop.log ntfy send lines (verbatim, every event kind)"
# Refuse to copy any send line that carries something URL-shaped: report positions only.
suspect_lines=$(grep -n 'notification' "$LOOP" | grep -E '://|ntfy\.sh' | cut -d: -f1 | paste -sd, -)
if [ -n "$suspect_lines" ]; then
  echo "FAIL: loop.log notification line(s) contain URL-shaped text at line number(s): $suspect_lines"
  echo "Content not printed. Stopping."
  exit 1
fi
grep -E 'notification (sent|not sent) ' "$LOOP"

echo
echo "== 4. checks"
failed=()

if [ "$done_count" -lt 1 ]; then
  failed+=("M7-AC1: no milestone has status DONE in state.json")
fi
if [ "$commit_count" -lt 1 ]; then
  failed+=("M7-AC1: main..$BRANCH has no commits")
fi
if ! grep -qE 'notification sent \(ntfy HTTP 200\): \[[^]]*\] [^ ]+ starting — ' "$LOOP"; then
  failed+=("M7-AC2: no HTTP 200 milestone-start notification in loop.log")
fi
if ! grep -qE 'notification sent \(ntfy HTTP 200\): \[[^]]*\] [^ ]+ DONE — ' "$LOOP"; then
  failed+=("M7-AC2: no HTTP 200 milestone-finish notification in loop.log")
fi
if ! grep -qE 'notification sent \(ntfy HTTP 200\): \[[^]]*\] implement loop stopped: ' "$LOOP"; then
  failed+=("M7-AC2: no HTTP 200 stop notification in loop.log")
fi

if [ "${#failed[@]}" -eq 0 ]; then
  echo "all checks passed"
  echo EVIDENCE_OK
  exit 0
fi
for reason in "${failed[@]}"; do
  echo "CHECK FAILED: $reason"
done
exit 1
