#!/usr/bin/env python3
"""Static contract tests for what happens when `maxTurns` cuts a subagent off.

Field evidence, P2-M7ad and P2-M7ae on OpenCodeOpenWeightHarness (2026-09-09):
every observed mid-generation cut-off sat at or just above its own agent's
configured ceiling — workers with `maxTurns: 40` cut off at 40, 44 and 44 tool
uses; a reviewer with `maxTurns: 50` cut off at 58, while the attempt that
finished came in at 45. Tool uses run ahead of turns because parallel calls batch
within a turn.

Two consequences the harness has to encode:

* A guard the model enforces by counting its own tool uses cannot be relied on —
  worker (32/40), reviewer (42/50) and navigator (8/10) all overran theirs. The
  protection has to be on disk, which is why the reviewer now persists as it goes
  the way the worker already did.
* A review that never finished routed nothing, so it is not a spent cycle, and
  the review loop needs the branch the fix cycle's CONTINUE already had.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]

BLOCK_ONCE_AGENTS = ("agents/reviewer.md", "agents/worker.md", "agents/verifier.md")


class ReviewerPersistsAsItGoesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reviewer = (ROOT / "agents/reviewer.md").read_text()

    def test_results_are_appended_the_moment_they_are_reached(self):
        self.assertIn("### Persisting as you go", self.reviewer)
        self.assertIn("<report path>.partial.md", self.reviewer)
        self.assertIn("the moment you reach it", self.reviewer)
        self.assertIn("Never\nhold results only in context", self.reviewer)

    def test_the_partial_is_removed_on_a_terminal_verdict(self):
        # Otherwise the caller cannot tell a live partial from a stale one.
        self.assertIn("rm -f <report path>.partial.md", self.reviewer)

    def test_self_counting_is_named_as_the_unreliable_part(self):
        # The reviewer already carried "at tool turn 42"; it overran it. The file
        # must say why that guard is second, not first.
        self.assertIn("Counting your own turns does not protect", self.reviewer)
        self.assertIn("second line of defence", self.reviewer)

    def test_a_truncated_return_is_the_same_state_as_INCOMPLETE(self):
        self.assertIn("A truncated return carrying\nno verdict", self.reviewer)

    def test_retry_policy_belongs_to_the_caller(self):
        # One cap, in the loop that owns the loop.
        self.assertIn("belong to the caller", self.reviewer)
        self.assertNotIn("may retry once", self.reviewer)

    def test_a_predecessors_partial_is_pointers_never_verdicts(self):
        self.assertIn("evidence pointers to re-confirm,\n  never verdicts to accept", self.reviewer)


class BlockOnceNeverPollTests(unittest.TestCase):
    @staticmethod
    def _flat(rel):
        # The rule wraps differently in each file; compare on collapsed
        # whitespace so a reflow does not read as a missing rule.
        return " ".join((ROOT / rel).read_text().split())

    def test_every_command_running_agent_is_told_to_block_once(self):
        # Two M7ad reviews were lost having backgrounded a 3m39s suite and spent
        # roughly twenty of their fifty turns polling it.
        for rel in BLOCK_ONCE_AGENTS:
            with self.subTest(agent=rel):
                flat = self._flat(rel)
                self.assertIn("blocking foreground call with a timeout that fits it", flat)
                self.assertIn("Never background it and poll for completion", flat)

    def test_the_cost_is_stated_in_turns(self):
        for rel in ("agents/worker.md", "agents/verifier.md"):
            with self.subTest(agent=rel):
                self.assertIn("Every poll costs a turn", self._flat(rel))


class ReviewLoopHandlesAnUnfinishedReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "skills/implement/SKILL.md").read_text()

    def test_the_loop_branches_on_a_review_that_did_not_finish(self):
        # Before this, the loop handled only PASS and CHANGES REQUIRED, and the
        # adjudication was done by hand on both occurrences.
        self.assertIn("IF it returns INCOMPLETE, or returns truncated with no verdict", self.skill)

    def test_an_unfinished_review_is_not_a_spent_cycle(self):
        self.assertIn("Do NOT increment ### Review Cycles. The cap counts reviews whose", self.skill)

    def test_the_truncated_text_is_never_mined_for_findings(self):
        self.assertIn("Do NOT mine the truncated text for findings", self.skill)

    def test_it_confirms_the_review_changed_nothing(self):
        self.assertIn("working tree clean, HEAD unmoved, no", self.skill)

    def test_the_retry_is_fresh_same_scope_and_capped(self):
        self.assertIn("invoke a FRESH harness:reviewer for the SAME cycle", self.skill)
        self.assertIn("Cap this at 2 retries per cycle", self.skill)

    def test_the_retry_is_handed_the_partial(self):
        self.assertIn("`<that path>.partial.md`", self.skill)

    def test_the_cycle_cap_rule_it_leans_on_still_exists(self):
        # The INCOMPLETE branch cites this rule; if it is ever reworded the
        # branch's justification goes with it.
        self.assertIn("whose findings were routed and fixed counts", self.skill)


if __name__ == "__main__":
    unittest.main()
