# Milestones

## M1 — Selecting a profile updates the view

Status: REVIEW

### Outcome

`select_profile` records the selection, dispatches the event, and the view
reflects the change.

### Architecture

N/A

### As-Built

N/A

### Acceptance Criteria

- [ ] `select_profile(view, "fast")` dispatches `("profile.selected", "fast")`
- [ ] `select_profile(view, "fast")` sets `view.selected` to `"fast"`
- [ ] After `select_profile(view, "fast")` returns, and with nothing else
      called, `view.displayed` is `"Profile: fast"`

### Baseline

BASELINE_SHA (branch: main)

### Evidence

- `profile.py` — `dispatch`, `ProfileView`, `select_profile`.
- `test_profile.py` — three tests, one per acceptance criterion.

Task tiers: T1 — Cheap (haiku), attempt 1, PASS.

### Validation

`python3 -m unittest discover -p 'test_*.py'` → 3 tests, OK, exit 0.
All three acceptance criteria have a named test.

### Review

Not yet reviewed.

### Review Cycles

0

### Follow-ups

None
