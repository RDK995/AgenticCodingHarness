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

- `inventory/ledger.py` — `Ledger`, `InsufficientStock`.
- `tests/test_ledger.py` — 3 tests, all passing.

Tasks and tiers:
- T1 — `Ledger.apply` and the on-hand count. **Cheap tier (haiku)**, attempt 1,
  accepted.
- T2 — the guarded withdrawal. **Cheap tier (haiku)**, attempt 1, accepted.
- T3 — `history()`. **Cheap tier (haiku)**, attempt 1, accepted.

### Validation

```
$ python3 -m unittest discover -s tests
Ran 3 tests in 0.000s

OK
```

### Review

**Cycle 1, attempt 1 — INCOMPLETE.** The reviewer was cut off by the runtime's
turn cap with no verdict and no per-criterion table returned. It changed
nothing: `HEAD` is unmoved and no report was written. What it had graded before
the cut-off is on disk at
`.harness/reviews/M1-cycle1.md.partial.md`.

`### Review Cycles` is **not** incremented for it — the cap counts reviews whose
findings were routed and fixed, and this one routed nothing.

### Review Cycles
0

### Follow-ups

None recorded.
