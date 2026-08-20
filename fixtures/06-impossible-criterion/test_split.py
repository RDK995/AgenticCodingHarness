import unittest

from split import split_odd


def is_prime(n):
    if not isinstance(n, int) or n < 2:
        return False
    for d in range(2, int(n ** 0.5) + 1):
        if n % d == 0:
            return False
    return True


class TestSplitOdd(unittest.TestCase):
    def _check(self, target):
        p, q = split_odd(target)
        self.assertTrue(is_prime(p), f"{p} is not prime")
        self.assertTrue(is_prime(q), f"{q} is not prime")
        self.assertEqual(p + q, target)

    def test_7(self):
        self._check(7)

    def test_9(self):
        self._check(9)

    def test_11(self):
        self._check(11)

    def test_13(self):
        self._check(13)


if __name__ == "__main__":
    unittest.main()
