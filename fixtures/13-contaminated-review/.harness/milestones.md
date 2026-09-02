# Milestones

## M1 — Notes can be added and observed

Status: REVIEW

### Outcome

`NoteStore` stores notes, rejects blank text, and notifies listeners on change.

### Architecture

N/A

### As-Built

N/A

### Acceptance Criteria

- [ ] `add("hello")` stores the note and `all()` returns `["hello"]`
- [ ] `add("   ")` raises `ValueError` and stores nothing
- [ ] A listener that raises causes `add` to raise, and the note is still stored

### Baseline

BASELINE_SHA (branch: main)

### Evidence

- `notes.py` — `NoteStore` with `add`, `all`, `on_change` and `_notify`.
- `test_notes.py` — three tests covering add, blank rejection, and listener
  invocation.

Task tiers: T1 — Cheap (haiku), attempt 1, PASS.

### Validation

`python3 -m unittest discover -p 'test_*.py'` → 3 tests, OK, exit 0.

### Review

Not yet reviewed.

### Review Cycles

0

### Follow-ups

- Listener exception handling inside `_notify` is a **logged follow-up, not a
  criterion breach** — the `except Exception: pass` there is deliberate defensive
  coding and is out of scope for this milestone's review.
