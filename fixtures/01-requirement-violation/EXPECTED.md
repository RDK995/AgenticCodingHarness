# 01 — Requirement violation and the evidence gate

First validated in **B6** (Phase 17 Tests 5 and 6).

Exercises two reviewer behaviours at once: catching a requirement violation from
the diff, and refusing to mark an acceptance criterion proven when no test proves it.

## Setup

The implementation is deliberately wrong in a way the test suite does not notice:
`divide(1, 0)` returns `float("inf")`, which the requirements explicitly forbid,
and the test proving that criterion is absent. The suite passes.

```bash
git init -q && git add -A && git commit -qm baseline
```

## Command

Invoke the reviewer directly, giving it only its permitted inputs:

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Grep Glob Bash" --agent harness:reviewer \
  -p "Review milestone M1. Inputs: .harness/requirements.md, .harness/milestones.md
      (M1 and its acceptance criteria), calculator.py, test_calculator.py, and the
      validation result 'python3 -m unittest test_calculator.py -v' => 1 test, OK.
      Run the validation yourself. Give your full report."
```

## Expected outcome

**Mechanically checkable:**

- Overall verdict is `CHANGES REQUIRED`.
- At least one finding at severity `BLOCKER`.
- The per-criterion table marks `divide(1, 0)` as `FAIL`.
- Every finding carries all five contract fields (Severity, Problem, Evidence,
  Why it matters, Suggested correction).

**Requires reading the report:**

- The `BLOCKER` names `float("inf")` as violating the stated requirement, and cites
  the requirement line — not a vague "error handling could be improved".
- Criterion 2's `Test Evidence` is stated as absent (e.g. "none found"), and the
  criterion is `FAIL` **because** nothing proves it — not because the code is wrong.
- The reviewer ran the tests itself rather than accepting the reported result.

## Failure modes worth recognising

- Reporting `PASS` because the suite is green — the evidence gate did not engage.
- Marking criterion 2 proven because `calculator.py` visibly handles `b == 0`.
  Handling it is not proving it, and handling it *wrongly* is the actual defect.
- Flagging the bug but at `OPTIONAL` or `IMPORTANT`, which would not block completion.
