# M1 — Review cycle 1

Verdict: CHANGES REQUIRED

## Acceptance criteria

| Criterion | Result |
| --- | --- |
| AC1 | PASS |
| AC2 | FAIL |
| AC3 | PASS |

## Findings

Severity:
IMPORTANT

Problem:
AC2 requires that a rejected withdrawal leaves `on_hand` and `history()`
unchanged. `inventory/ledger.py` implements the guard correctly, but no test
asserts the second half of the criterion. `tests/test_ledger.py` contains
`test_rejects_oversized_withdrawal`, which asserts only that
`InsufficientStock` is raised.

Evidence:
`tests/test_ledger.py`

Why it matters:
A criterion with no test proving it is not proven. The implementation is right
today and nothing would catch it becoming wrong.

Suggested correction:
Add a test that applies an oversized withdrawal, catches `InsufficientStock`,
and then asserts `on_hand` and `history()` are what they were before the call.
