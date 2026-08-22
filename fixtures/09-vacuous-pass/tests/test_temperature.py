import unittest

from temperature import to_celsius


class TestToCelsius(unittest.TestCase):
    def test_boiling_point(self):
        self.assertEqual(to_celsius(212), 100.0)

    def test_freezing_point(self):
        self.assertEqual(to_celsius(32), 0.0)


if __name__ == "__main__":
    unittest.main()
