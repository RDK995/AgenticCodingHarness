#!/usr/bin/env python3
"""Static contract tests for bounded harness subagents."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIMITS = {
    "navigator.md": 10,
    "orchestrator.md": 30,
    "worker.md": 40,
    "verifier.md": 35,
    "reviewer.md": 50,
    "as-built.md": 30,
}


def frontmatter(path: Path) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(), re.DOTALL)
    if not match:
        raise AssertionError(f"missing frontmatter: {path}")
    result = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


class AgentGuardTests(unittest.TestCase):
    def test_every_subagent_has_a_hard_cap_and_is_foreground(self):
        for filename, expected in LIMITS.items():
            with self.subTest(agent=filename):
                metadata = frontmatter(ROOT / "agents" / filename)
                self.assertEqual(int(metadata["maxTurns"]), expected)
                self.assertEqual(metadata["background"], "false")

    def test_soft_handoffs_precede_hard_caps(self):
        expected_phrases = {
            "orchestrator.md": "At 20",
            "worker.md": "tool turn 32",
            "verifier.md": "tool turn 28",
            "reviewer.md": "tool turn 42",
            "navigator.md": "tool turn 8",
            "as-built.md": "tool turn 25",
        }
        for filename, phrase in expected_phrases.items():
            with self.subTest(agent=filename):
                self.assertIn(phrase, (ROOT / "agents" / filename).read_text())

    def test_controller_treats_missing_contract_as_interrupted(self):
        skill = (ROOT / "skills" / "implement" / "SKILL.md").read_text()
        self.assertIn("missing its required terminal field", skill)
        self.assertIn("INTERRUPTED", skill)


if __name__ == "__main__":
    unittest.main()
