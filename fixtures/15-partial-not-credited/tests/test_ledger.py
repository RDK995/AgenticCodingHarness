import unittest

from inventory.ledger import InsufficientStock, Ledger


class LedgerTests(unittest.TestCase):
    def test_apply_updates_the_on_hand_count(self):
        led = Ledger()
        led.apply(10, "delivery")
        self.assertEqual(led.on_hand, 10)

    def test_rejects_oversized_withdrawal(self):
        led = Ledger()
        led.apply(3, "delivery")
        with self.assertRaises(InsufficientStock):
            led.apply(-5, "sale")

    def test_history_is_oldest_first(self):
        led = Ledger()
        led.apply(4, "first")
        led.apply(-1, "second")
        self.assertEqual([note for _, note in led.history()], ["first", "second"])


if __name__ == "__main__":
    unittest.main()
