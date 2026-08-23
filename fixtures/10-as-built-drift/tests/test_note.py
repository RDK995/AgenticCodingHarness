import os
import pathlib
import tempfile
import unittest

_TMP = tempfile.mkdtemp()
os.environ["NOTE_HOME"] = _TMP

from note import cli, store  # noqa: E402


class NoteTests(unittest.TestCase):
    def setUp(self):
        path = store.storage_path()
        if path.exists():
            path.unlink()

    def test_add_then_list_survives_restart(self):
        cli.main(["add", "buy milk"])
        self.assertEqual(store.read_all(), ["buy milk"])

    def test_empty_text_rejected(self):
        self.assertEqual(cli.main(["add", "   "]), 1)

    def test_list_with_no_notes_exits_zero(self):
        self.assertEqual(cli.main(["list"]), 0)

    def test_search_filters_case_insensitively(self):
        cli.main(["add", "Buy Milk"])
        cli.main(["add", "call dentist"])
        self.assertEqual(cli.main(["search", "MILK"]), 0)

    def test_search_returns_only_matches(self):
        cli.main(["add", "buy milk"])
        cli.main(["add", "call dentist"])
        from note import search
        self.assertEqual(search.matching("milk"), ["buy milk"])


if __name__ == "__main__":
    unittest.main()
