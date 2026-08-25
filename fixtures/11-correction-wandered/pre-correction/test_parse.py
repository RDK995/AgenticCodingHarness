import unittest

from receipt.parse import AmountError, parse_amount


class ParseTest(unittest.TestCase):
    def test_exact_cents(self):
        self.assertAlmostEqual(parse_amount("19.99"), 19.99)

    def test_single_penny(self):
        self.assertAlmostEqual(parse_amount("0.07"), 0.07)

    def test_malformed_raises(self):
        with self.assertRaises(AmountError):
            parse_amount("twelve")
