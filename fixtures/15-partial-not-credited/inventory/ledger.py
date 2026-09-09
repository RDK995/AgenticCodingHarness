"""A stock ledger: on-hand counts, guarded withdrawals, and an audit trail."""


class InsufficientStock(Exception):
    """Raised when a withdrawal exceeds what is on hand."""


class Ledger:
    def __init__(self):
        self._on_hand = 0
        self._history = []

    @property
    def on_hand(self):
        return self._on_hand

    def apply(self, delta, note=""):
        """Apply a signed change to the on-hand count and record it."""
        self._on_hand += delta
        self._history.append((delta, note))
        if self._on_hand < 0:
            raise InsufficientStock(
                "withdrawal of %d exceeds %d on hand"
                % (-delta, self._on_hand - delta)
            )
        return self._on_hand

    def history(self):
        """Every applied change, oldest first."""
        return list(self._history)
