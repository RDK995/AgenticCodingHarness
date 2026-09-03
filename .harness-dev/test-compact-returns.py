#!/usr/bin/env python3
"""Static tests for report ownership and compact controller returns."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CompactReturnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reviewer = (ROOT / "agents" / "reviewer.md").read_text()
        cls.skill = (ROOT / "skills" / "implement" / "SKILL.md").read_text()

    def test_reviewer_owns_changes_required_artifact(self):
        self.assertIn("write the complete table and findings yourself", self.reviewer)
        self.assertIn("Report: .harness/reviews/", self.reviewer)
        self.assertIn("never use it outside that directory", self.reviewer)

    def test_reviewer_returns_a_compact_envelope(self):
        for field in ("Verdict:", "Report:", "Per-Criterion:", "Findings:", "Result:"):
            self.assertIn(field, self.reviewer)
        self.assertIn("not the report body", self.reviewer)

    def test_pass_writes_no_report(self):
        self.assertIn("On `PASS`, write no report", self.reviewer)
        self.assertIn("Report: NONE", self.reviewer)

    def test_controller_never_relays_report_body(self):
        self.assertNotIn("write its report verbatim to .harness/reviews/M<n>", self.skill)
        self.assertIn("Do NOT write, read, quote or reproduce the report", self.skill)
        self.assertIn("Never write a review report yourself", self.skill)


if __name__ == "__main__":
    unittest.main()
