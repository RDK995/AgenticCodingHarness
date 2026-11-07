#!/usr/bin/env python3
"""Static checks for the /harness:implement-loop skill file."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "implement-loop" / "SKILL.md"

COMMANDS = [
    'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/implement-loop.py" start',
    'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/implement-loop.py" status',
    'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/implement-loop.py" stop',
]


class ImplementLoopSkillTests(unittest.TestCase):
    def test_skill_file_exists(self):
        self.assertTrue(SKILL.is_file(), f"missing {SKILL}")

    def test_frontmatter_has_name_and_description(self):
        text = SKILL.read_text(encoding="utf-8")
        parts = text.split("---\n", 2)
        self.assertGreaterEqual(len(parts), 3, "frontmatter must be delimited by --- lines")
        self.assertEqual(parts[0], "", "file must start with the --- frontmatter line")
        fields = {}
        for line in parts[1].splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                fields[key.strip()] = value.strip()
        self.assertEqual(fields.get("name"), "implement-loop")
        self.assertTrue(fields.get("description"), "description must be non-empty")

    def test_body_contains_each_driver_command(self):
        body = SKILL.read_text(encoding="utf-8").split("---\n", 2)[2]
        for command in COMMANDS:
            self.assertIn(command, body)


if __name__ == "__main__":
    unittest.main()
