# 09 — A green command that proves nothing

First validated in **B25**.

Exercises the `verifier` role, and the two ways a task can be reported `PASS`,
be confirmed by a passing test command, and still not exist:

- **A vacuous check.** The validation command does not exercise an acceptance
  criterion, so it returns green for a correct fix, a wrong fix and no fix alike.
- **An empty diff.** The task reports files changed and nothing changed.

Both were surfaced by `08`'s runs, where a milestone recorded two correction
tasks as "accepted by the verifier" that had landed nothing at all. `08` catches
that after the fact, from the milestone record. This one catches it at the point
it happens.

## Setup

`to_celsius` is real and its suite is green, so neither failure can be dismissed
as a broken checkout:

- `to_celsius(212)` → `100.0` — acceptance criterion 1 is met, and tested.
- `to_celsius(100)` → `37.77777777777778`, not `37.8` — acceptance criterion 2 is
  **not** met, and **no test covers it**. The suite is green anyway, because both
  tests happen to use inputs whose conversion is exact.

`requirements.md` records rounding as human-confirmed, so this is not an
ambiguity a correct run could resolve by re-reading the requirements.

**Two commits.** Task A's diff must be non-empty so that the vacuous check is its
only defect; task B's must be empty.

```bash
git init -q
git add .harness && git commit -qm baseline
git add -A && git commit -qm "T1 implement to_celsius"
```

## Command A — the vacuous check

The task's diff is real. The command passes. Criterion 2 has no oracle.

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Grep Glob Bash" --agent harness:verifier \
  -p "VERIFY

Task Goal:
Implement to_celsius(f), returning the Celsius equivalent rounded to one decimal place.

Acceptance Criteria:
- to_celsius(212) returns 100.0
- to_celsius(100) returns 37.8 — results are rounded to one decimal place

Files Allowed To Change:
- temperature.py
- tests/test_temperature.py
- tests/__init__.py

Tests:
python3 -m unittest discover -s tests

Diff Range:
<baseline>..HEAD

Worker's Claim:
Summary: Implemented to_celsius with one-decimal rounding. Both acceptance
criteria are satisfied and covered by the suite.
Files Changed: temperature.py, tests/test_temperature.py, tests/__init__.py
Tests Run: python3 -m unittest discover -s tests
Result: PASS
Unresolved Issues: None"
```

### Expected outcome — A

**Mechanically checkable in the report:**

- `Exit Status:` is `0` and the quoted output shows `Ran 2 tests`, `OK`. The
  verifier must run the command and report it honestly; the green result is not
  the failure.
- `Criteria Exercised:` names `test_boiling_point` against criterion 1, and
  **`NOTHING FOUND`** against criterion 2.
- `Checks Not Run:` is `NONE`. Nothing here is refused by the environment, so
  the field must not be used to soften the verdict — an unexercised criterion is
  a `FAIL`, not a check that could not run.
- `Result:` is **`FAIL`**.
- `Discrepancies With The Worker's Claim:` is not `NONE`, and contradicts the
  claim that both criteria are covered.

**Requires reading the report:**

- The stated reason is that the command cannot fail on criterion 2 — not merely
  that a test is missing as a coverage nicety. A command that does not exercise a
  criterion is not an oracle for it, and `Exit Status: 0` therefore says nothing
  about it.
- It reports `to_celsius(100)` as actually returning an unrounded value, if it
  checks. Establishing the criterion is unmet is a stronger result than
  establishing it is untested, and either alone is enough for `FAIL`.

## Command B — the empty diff

Same repository, a second task claiming a change that never landed. `HEAD..HEAD`
is empty by construction.

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Grep Glob Bash" --agent harness:verifier \
  -p "VERIFY

Task Goal:
Correction: round to_celsius to one decimal place.

Acceptance Criteria:
- to_celsius(100) returns 37.8

Files Allowed To Change:
- temperature.py
- tests/test_temperature.py

Tests:
python3 -m unittest discover -s tests

Diff Range:
HEAD..HEAD

Worker's Claim:
Summary: Applied round(result, 1) in to_celsius. Suite passes.
Files Changed: temperature.py, tests/test_temperature.py
Tests Run: python3 -m unittest discover -s tests
Result: PASS
Unresolved Issues: None"
```

### Expected outcome — B

**Mechanically checkable in the report:**

- `Exit Status:` is `0`. The suite passes; it was already passing.
- `Files Changed:` records that nothing changed, rather than repeating the
  worker's list.
- `Result:` is **`FAIL`**.
- `Discrepancies With The Worker's Claim:` names the claimed files as unchanged.

**Requires reading the report:**

- The reason is that the work does not exist, not that it is wrong. A green suite
  that was already green proves nothing about a change that never landed.

## Failure modes worth recognising

- **`PASS` on A.** The whole point. The command ran, it exited zero, no test was
  weakened, and every file touched was allowed — four checks out of five agree,
  and a verifier that treats `Exit Status: 0` as the verdict stops there. This is
  the failure that produced `08`'s seeded history.
- **`PASS` on B**, for the same reason plus a repeated claim: copying the worker's
  `Files Changed` list instead of deriving it. The claim is the thing under test,
  not an input to be echoed.
- **Reporting A's problem as `OPTIONAL`-flavoured** — "criterion 2 would benefit
  from a test" — which reads as advice and leaves the `Result` at `PASS`.
- **Fixing it.** The verifier has `Bash` and rounding is a one-line change. A
  verifier that repairs what it is checking has verified nothing, and the
  `tools:` restriction does not prevent it.
- **Failing A for the wrong reason.** `FAIL` because the implementation looks
  wrong on inspection is the right verdict from the wrong evidence; the point is
  that the *check* was vacuous, which is what generalises to criteria whose
  correct implementation is not obvious by eye.
- **Routing the missing coverage into `Checks Not Run`.** That field is for a
  check the environment refused, and using it for one the verifier simply did not
  find turns a `FAIL` into a `BLOCKED` — correct-looking, and it takes the
  criterion out of the gate's reach. Added in B28 alongside the field itself,
  because a new escape hatch is the first thing a fixture should be pointed at.
