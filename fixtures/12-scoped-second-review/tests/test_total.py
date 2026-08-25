import unittest

from receipt.total import total


class TotalTest(unittest.TestCase):
    def test_hundred_pennies_is_exact(self):
        self.assertEqual(total([7] * 100), 700)
