import unittest

from receipt.total import total


class TotalTest(unittest.TestCase):
    def test_hundred_pennies_is_exact(self):
        self.assertAlmostEqual(total([0.07] * 100), 7.00)
