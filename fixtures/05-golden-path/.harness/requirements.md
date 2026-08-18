# Requirements

## Goal

Add a calculator function that divides two numbers.

## Functional Requirements

- Provide a `divide(a, b)` function.
- Division by zero must raise an error, not return `Infinity`, `NaN`, or `None`.

## Acceptance Criteria

- `divide(6, 2)` returns `3.0`
- `divide(1, 0)` raises an error

## Constraints

- Python 3, standard library only — no new dependencies.

## Non-Goals

- Add/subtract/multiply are out of scope.

## Edge Cases

- `b == 0` (including `0.0` and `-0.0`)

## Decisions / Clarifications

- Division by zero raises rather than returning a sentinel — confirmed.

## Open Questions

None
