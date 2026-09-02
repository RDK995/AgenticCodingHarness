import unittest

from notes import NoteStore


class NoteStoreTest(unittest.TestCase):
    def test_add_stores_the_note(self):
        s = NoteStore()
        s.add("hello")
        self.assertEqual(s.all(), ["hello"])

    def test_empty_note_is_rejected(self):
        s = NoteStore()
        with self.assertRaises(ValueError):
            s.add("   ")

    def test_listener_is_called_on_add(self):
        s = NoteStore()
        seen = []
        s.on_change(lambda notes: seen.append(notes))
        s.add("hello")
        self.assertEqual(len(seen), 1)


if __name__ == "__main__":
    unittest.main()
