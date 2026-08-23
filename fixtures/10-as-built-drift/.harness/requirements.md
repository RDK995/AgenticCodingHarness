# Requirements

## Status

AGREED

## Functional Requirements

- `note add <text>` stores a note. Empty text is rejected with exit code 1.
- `note list` prints every note, oldest first, one per line. No notes prints
  nothing and exits 0.
- `note search <term>` prints only notes containing `term` (case-insensitive),
  in the same order as `list`.
- Notes survive process restart.

## Constraints

- Python 3, standard library only.
- Single user, single machine.

## Non-Goals

- Editing or deleting notes.
- Any network or multi-user behaviour.

## Open Questions

None
