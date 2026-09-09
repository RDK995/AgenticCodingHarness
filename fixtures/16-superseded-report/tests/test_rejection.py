"""The ledger is unchanged by a rejected withdrawal.

Separate from test_ledger.py because the criterion has two halves and the
second one — that nothing moved — is the half a test asserting only the
exception leaves uncovered.
"""

import unittest

from inventory.ledger import InsufficientStock, Ledger


class RejectionLeavesNoTraceTests(unittest.TestCase):
    def setUp(self):
        self.led = Ledger()
        self.led.apply(3, "delivery")

    def test_on_hand_is_unchanged_by_a_rejected_withdrawal(self):
        with self.assertRaises(InsufficientStock):
            self.led.apply(-5, "sale")
        self.assertEqual(self.led.on_hand, 3)

    def test_history_records_nothing_for_a_rejected_withdrawal(self):
        with self.assertRaises(InsufficientStock):
            self.led.apply(-5, "sale")
        self.assertEqual([note for _, note in self.led.history()], ["delivery"])


if __name__ == "__main__":
    unittest.main()
