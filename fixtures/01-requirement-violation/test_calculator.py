import unittest

from calculator import divide


class TestDivide(unittest.TestCase):
    def test_divide_returns_float(self):
        self.assertEqual(divide(6, 2), 3.0)


if __name__ == "__main__":
    unittest.main()
