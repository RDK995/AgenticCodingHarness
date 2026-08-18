# Milestones

## M1 — Notes can be added and listed, and survive restart

Status: REVIEW

### Outcome

A working `note` CLI: `note add <text>` stores a note, `note list` prints all
notes newest first, and notes persist across process runs.

### Architecture

C1, C2

### Acceptance Criteria
- [ ] A note added in one process run is listed in a later run
- [ ] `note list` with no notes prints nothing and exits 0

### Evidence

`note/cli.py`, `note/store.py`, `note/__main__.py`, `tests/test_note.py`

### Validation

`python3 -m unittest discover -s tests -v` — 4 tests, all pass.

### Review

### Review Cycles
0

### Follow-ups
