Acceptance Criterion:
AC1 — `apply(10)` on an empty ledger leaves `on_hand` at 10

Implementation Evidence:
`inventory/ledger.py`, `Ledger.apply`

Test Evidence:
`tests/test_ledger.py::LedgerTests::test_apply_updates_the_on_hand_count`

Result:
PASS

Acceptance Criterion:
AC2 — A withdrawal exceeding stock raises `InsufficientStock` and leaves
`on_hand` and `history()` unchanged

Implementation Evidence:
`inventory/ledger.py`, `Ledger.apply` — the guard precedes the mutation

Test Evidence:
none found in `tests/test_ledger.py`

Result:
FAIL
