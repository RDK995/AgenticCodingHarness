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

- Add/subtract/multiply are out of scope for now.

## Edge Cases

- `b == 0` (including `0.0` and `-0.0`)

## Decisions / Clarifications

- Division by zero must raise an error rather than return a numeric sentinel
  like `Infinity`/`NaN`/`None` — confirmed with the human during roasting.
- Python 3, standard library only — confirmed with the human (no existing
  code in the repo to infer language/runtime from).

## Open Questions

None
