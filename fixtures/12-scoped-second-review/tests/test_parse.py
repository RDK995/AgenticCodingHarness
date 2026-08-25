import unittest

from receipt.parse import AmountError, parse_amount


class ParseTest(unittest.TestCase):
    def test_exact_cents(self):
        self.assertEqual(parse_amount("19.99"), 1999)

    def test_single_penny(self):
        self.assertEqual(parse_amount("0.07"), 7)

    def test_malformed_raises(self):
        with self.assertRaises(AmountError):
            parse_amount("twelve")

    def test_second_decimal_point_raises(self):
        with self.assertRaises(AmountError):
            parse_amount("1.2.3")

    def test_third_decimal_place_raises(self):
        with self.assertRaises(AmountError):
            parse_amount("1.234")
