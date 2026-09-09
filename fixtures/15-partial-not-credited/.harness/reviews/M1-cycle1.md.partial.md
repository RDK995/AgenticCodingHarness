Acceptance Criterion:
AC1 — `apply(10)` on an empty ledger leaves `on_hand` at 10

Implementation Evidence:
`inventory/ledger.py`, `Ledger.apply` — `self._on_hand += delta`

Test Evidence:
`tests/test_ledger.py::LedgerTests::test_apply_updates_the_on_hand_count`

Result:
PASS

Acceptance Criterion:
AC2 — A withdrawal exceeding stock raises `InsufficientStock` and leaves
`on_hand` and `history()` unchanged

Implementation Evidence:
`inventory/ledger.py`, `Ledger.apply` — raises `InsufficientStock` when the
resulting count would be negative

Test Evidence:
`tests/test_ledger.py::LedgerTests::test_rejects_oversized_withdrawal`

Result:
PASS
