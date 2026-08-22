# Requirements — temperature

## Goal

Convert Fahrenheit to Celsius.

## Functional Requirements

- `to_celsius(f)` returns the Celsius equivalent of `f`.
- The result is rounded to one decimal place.

## Acceptance Criteria

- [ ] `to_celsius(212)` returns `100.0`
- [ ] `to_celsius(100)` returns `37.8` — results are rounded to one decimal place

## Constraints

- Python 3, standard library only.

## Decisions / Clarifications

- Rounding was confirmed by the human as required. An unrounded float is a
  defect, not a presentational detail.

## Open Questions

None.
