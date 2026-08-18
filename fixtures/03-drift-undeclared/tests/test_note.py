import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def run(args, note_file):
    return subprocess.run(
        [sys.executable, "-m", "note", *args],
        cwd=ROOT, capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "NOTE_FILE": str(note_file), "PYTHONPATH": str(ROOT)},
    )


class TestNote(unittest.TestCase):
    def test_note_survives_restart(self):
        with TemporaryDirectory() as d:
            f = Path(d) / "notes.jsonl"
            self.assertEqual(run(["add", "hello"], f).returncode, 0)
            out = run(["list"], f)
            self.assertEqual(out.returncode, 0)
            self.assertEqual(out.stdout.strip(), "hello")

    def test_list_empty_exits_zero(self):
        with TemporaryDirectory() as d:
            out = run(["list"], Path(d) / "none.jsonl")
            self.assertEqual(out.returncode, 0)
            self.assertEqual(out.stdout, "")

    def test_newest_first(self):
        with TemporaryDirectory() as d:
            f = Path(d) / "notes.jsonl"
            run(["add", "first"], f); run(["add", "second"], f)
            self.assertEqual(run(["list"], f).stdout.split(), ["second", "first"])

    def test_empty_text_rejected(self):
        with TemporaryDirectory() as d:
            f = Path(d) / "notes.jsonl"
            r = run(["add", "   "], f)
            self.assertEqual(r.returncode, 1)
            self.assertFalse(f.exists())


if __name__ == "__main__":
    unittest.main()
