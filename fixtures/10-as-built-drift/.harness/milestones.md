# Milestones

## M1 — Notes can be added and listed, and survive restart

Status: DONE

### Outcome

`note add <text>` stores a note, `note list` prints every note oldest first, and
notes persist across process runs.

### Architecture

C1, C2

### As-Built

`.harness/as-built/M1.md` — RECORDED, 2 components, no claim mismatch

### Acceptance Criteria
- [x] A note added in one process run is listed in a later run
- [x] `note list` with no notes prints nothing and exits 0
- [x] Empty text is rejected with exit code 1

### Baseline

The fixture's initial `baseline` commit, on the default branch.

### Evidence

`note/cli.py`, `note/store.py`, `note/__main__.py`, `tests/test_note.py`.
Committed as `M1 — add and list`.

### Validation

`python3 -m unittest discover -s tests` — 5 tests, `OK`.

### Review

PASS at cycle 1. Reviewer confirmed C1 → C2 is the only boundary and that
persistence is owned by C2 alone.

### Review Cycles
1

### Follow-ups

None

## M2 — Notes can be searched

Status: DONE

### Outcome

`note search <term>` prints only the notes containing `term`, case-insensitively,
in the same order as `list`.

### Architecture

C2, C3

### As-Built

### Acceptance Criteria
- [x] `note search <term>` prints only matching notes
- [x] Matching is case-insensitive
- [x] Results keep insertion order

### Baseline

The `M1 — add and list` commit, on the default branch.

### Evidence

`note/search.py`, plus the `search` branch in `note/cli.py` and the two search
tests, which were already present at the M1 commit. **`note/search.py` is not
committed** — the milestone's work is in the working tree.

### Validation

`python3 -m unittest discover -s tests` — 5 tests, `OK`.

### Review

PASS at cycle 1.

### Review Cycles
1

### Follow-ups

None
