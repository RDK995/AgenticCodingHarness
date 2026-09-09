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
        """Apply a signed change to the on-hand count and record it.

        The guard runs before anything is mutated: a rejected withdrawal
        leaves the ledger indistinguishable from one where it was never
        called.
        """
        if self._on_hand + delta < 0:
            raise InsufficientStock(
                "withdrawal of %d exceeds %d on hand" % (-delta, self._on_hand)
            )
        self._on_hand += delta
        self._history.append((delta, note))
        return self._on_hand

    def history(self):
        """Every applied change, oldest first."""
        return list(self._history)
