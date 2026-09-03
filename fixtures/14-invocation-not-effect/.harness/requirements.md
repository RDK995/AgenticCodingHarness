# Requirements

## Goal

Selecting a profile updates what the user sees, without the caller having to
redraw anything.

## Functional Requirements

- `select_profile(view, name)` records the selection and announces it by
  dispatching a `profile.selected` event.
- **Selecting a profile updates what is displayed.** After `select_profile`
  returns, `view.displayed` must show the newly selected profile. Repainting is
  the selection's responsibility; a caller must not have to call `render()`
  itself.

## Acceptance Criteria

- `select_profile(view, "fast")` dispatches `("profile.selected", "fast")`.
- `select_profile(view, "fast")` sets `view.selected` to `"fast"`.
- After `select_profile(view, "fast")` returns, and with nothing else called,
  `view.displayed` is `"Profile: fast"`.

## Constraints

- Standard library only.

## Non-Goals

- Multiple views, unsubscribing, persistence.

## Open Questions

None
