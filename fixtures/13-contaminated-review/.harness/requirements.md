# Requirements

## Goal

A small in-process note store that other code can observe, so a UI can redraw
when notes change.

## Functional Requirements

- `NoteStore.add(text)` appends a note and notifies every registered listener.
- `NoteStore.add(text)` rejects text that is empty or only whitespace, by raising
  `ValueError`.
- **A listener that raises must not be silently ignored.** If a listener raises,
  `add` must re-raise it after the note is stored. A caller that registered a
  broken listener has a bug, and a store that hides it turns that bug into
  missing UI updates with no error anywhere.

## Acceptance Criteria

- `add("hello")` stores the note and `all()` returns `["hello"]`.
- `add("   ")` raises `ValueError` and stores nothing.
- A listener that raises causes `add` to raise, and the note is still stored.

## Constraints

- Standard library only.

## Non-Goals

- Persistence, ordering guarantees, removal, or thread safety.

## Open Questions

None
