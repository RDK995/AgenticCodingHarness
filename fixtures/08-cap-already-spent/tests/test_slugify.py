import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_spaces_become_hyphens(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_lowercased(self):
        self.assertEqual(slugify("HELLO"), "hello")

    def test_punctuation_dropped(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")


if __name__ == "__main__":
    unittest.main()
