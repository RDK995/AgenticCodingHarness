# Milestones

## M1 — A stock ledger with a guarded withdrawal

Status: REVIEW

### Outcome

`Ledger` tracks on-hand stock, rejects a withdrawal larger than stock, and
reports its history oldest-first.

### Architecture

N/A

### Acceptance Criteria
- [ ] `apply(10)` on an empty ledger leaves `on_hand` at 10
- [ ] A withdrawal exceeding stock raises `InsufficientStock` and leaves
      `on_hand` and `history()` unchanged
- [ ] `history()` returns applied changes oldest first

### Baseline

BASELINE_SHA on m1-ledger

### Evidence

- `inventory/ledger.py` — `Ledger`, `InsufficientStock`. The guard runs before
  any mutation.
- `tests/test_ledger.py` — 3 tests.
- `tests/test_rejection.py` — 2 tests, covering the half of AC2 that says the
  ledger is left unchanged.

Tasks and tiers:
- T1 — `Ledger.apply` and the on-hand count. **Cheap tier (haiku)**, attempt 1,
  accepted.
- T2 — the guarded withdrawal, and `tests/test_rejection.py` with it. **Cheap
  tier (haiku)**, attempt 1, accepted.
- T3 — `history()`. **Cheap tier (haiku)**, attempt 1, accepted.

### Validation

```
$ python3 -m unittest discover -s tests
Ran 5 tests in 0.000s

OK
```

### Review

**Cycle 1, attempt 1 — INCOMPLETE.** The reviewer was cut off by the runtime's
turn cap. The cut-off landed **after** it had written its report — the report at
`.harness/reviews/M1-cycle1.md` is that attempt's, and no envelope was ever
returned for it. Its partial is at `.harness/reviews/M1-cycle1.md.partial.md`.

Nothing downstream has consumed either file. No correction has been routed and
`HEAD` is unmoved: the completion gate consumes the returned envelope, not the
file on disk, so a report with no envelope behind it is not a review.

`### Review Cycles` is **not** incremented for it — the cap counts reviews whose
findings were routed and fixed, and this one routed nothing.

### Review Cycles
0

### Follow-ups

None recorded.
