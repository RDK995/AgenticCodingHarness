# Milestones

## M1 — Callers can divide two numbers, and division by zero raises

Status: REVIEW

### Outcome

A `divide(a, b)` function returning the quotient as a float, raising an error
when the divisor is zero rather than returning a numeric sentinel.

### Architecture

N/A

### Acceptance Criteria
- [ ] `divide(6, 2)` returns `3.0`
- [ ] `divide(1, 0)` raises an error

### Baseline

The fixture's initial `baseline` commit, on the default branch.

### Evidence

`calculator.py`, `test_calculator.py`

### Validation

`python3 -m unittest test_calculator.py -v` — 1 test, passes.

### Review

### Review Cycles
0

### Follow-ups
