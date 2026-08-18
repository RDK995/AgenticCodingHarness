# Requirements

## Goal

A command-line tool that records short notes and lists them back.

## Functional Requirements

- `note add <text>` stores a note.
- `note list` prints all stored notes, newest first.
- Notes survive restarting the tool.

## Acceptance Criteria

- A note added in one process run is listed in a later run.
- `note list` with no notes prints nothing and exits 0.

## Constraints

- Python 3, standard library only — no new dependencies.

## Non-Goals

- No editing or deleting notes.
- No multi-user support, no sync.

## Edge Cases

- Empty note text.
- Storage file missing or unreadable on first run.

## Decisions / Clarifications

- Single local user, single machine — confirmed with the human.

## Open Questions

None
