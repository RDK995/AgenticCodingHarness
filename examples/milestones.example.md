# Milestones

## M1 — Calculator division is available and safe against division by zero

Status: DONE

### Outcome

A `divide(a, b)` function exists in the codebase (Python 3, standard library
only) that returns the correct quotient for valid inputs and raises an error
instead of returning `Infinity`/`NaN`/`None` when `b == 0`.

### Architecture

N/A

### Acceptance Criteria
- [x] divide(6, 2) returns 3.0
- [x] divide(1, 0) raises an error

### Baseline

`a1b2c3d` on `main`

### Evidence

- `calculator.py` (new) — `divide(a, b)` returns `a / b` as a float; raises
  `ZeroDivisionError("Cannot divide by zero")` when `b == 0` (covers `0.0` and
  `-0.0` since `b == 0` is `True` for both).
- `tests/test_calculator.py` (new) — `test_divide_valid_inputs` asserts
  `divide(6, 2) == 3.0`; `test_divide_by_zero_raises_error` asserts
  `divide(1, 0)` raises `ZeroDivisionError`.
- No `add`/`subtract`/`multiply` functions added (non-goal respected). No
  third-party dependencies.

### Validation

- `python3 -m unittest discover -s tests -v` → `Ran 2 tests in 0.000s — OK`
  (run independently by both the orchestrator and the reviewer).
- Manual interpreter check: `divide(6, 2)` → `3.0` (`float`); `divide(1, 0)` →
  raises `ZeroDivisionError: Cannot divide by zero`; `divide(1, 0.0)` and
  `divide(1, -0.0)` also raise.
- `git status`/`git diff` confirmed only `calculator.py` and `tests/` were
  touched — no unrelated files changed.

### Review

Fresh-context review (harness:reviewer): PASS. Both acceptance criteria
independently verified with implementation + test evidence; stdlib-only
constraint confirmed; non-goal respected; no unrelated files touched. No
BLOCKER, IMPORTANT, or OPTIONAL findings.

### Review Cycles
1

### Follow-ups

None.
