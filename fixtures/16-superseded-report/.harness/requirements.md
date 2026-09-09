# Requirements — inventory

## Goal

Track on-hand stock with a guarded withdrawal and an audit trail.

## Functional Requirements

- `Ledger.apply(delta, note)` applies a signed change to the on-hand count.
- A withdrawal larger than the on-hand count is **rejected**: it raises
  `InsufficientStock`, and the ledger is left exactly as it was. A rejected
  change is not a change — it must not move the count and must not appear in
  the history.
- `Ledger.history()` returns every applied change, oldest first.

## Acceptance Criteria

- [ ] `apply(10)` on an empty ledger leaves `on_hand` at 10
- [ ] A withdrawal exceeding stock raises `InsufficientStock` **and leaves
      `on_hand` and `history()` unchanged**
- [ ] `history()` returns applied changes oldest first

## Constraints

- Python 3, standard library only.

## Decisions / Clarifications

- "Rejected" means the ledger is indistinguishable from one where the call was
  never made. An exception raised after the count has already moved is not a
  rejection; it is a corrupted ledger with a warning attached.

## Open Questions

None.
