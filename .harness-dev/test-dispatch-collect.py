#!/usr/bin/env python3
"""Static contract tests for the orchestrator's dispatch-and-collect rule.

The rule exists because `Agent` dispatch is asynchronous: it returns an agentId in
about two seconds, and an orchestrator that ends its turn to wait is re-entered by
the completion notification with a fresh turn allowance on the context it already
holds. Measured on 24 field sessions (2026-09-08 record): 318 segments, none over
the 30-turn cap, one context at 147 turns, 53% of orchestrator traffic accruing
past cumulative turn 30.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DispatchCollectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orchestrator = (ROOT / "agents/orchestrator.md").read_text()

    def test_collection_blocks_instead_of_ending_the_turn(self):
        for phrase in (
            "TaskOutput",
            "block: true",
            "timeout: 600000",
            'ToolSearch("select:TaskOutput")',
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.orchestrator)

    def test_dispatch_stays_parallel(self):
        # Blocking on collection must not serialise dispatch: 88% of measured
        # orchestrator contexts had two or more agents outstanding at once.
        self.assertIn("Dispatch everything that can run at once", self.orchestrator)
        self.assertIn("They run concurrently", self.orchestrator)

    def test_waiting_by_sleeping_or_polling_is_forbidden(self):
        self.assertIn(
            "Never wait by sleeping, by polling a file, or by arming a Monitor",
            self.orchestrator,
        )

    def test_the_turn_never_ends_on_an_uncollected_dispatch(self):
        # 2 of 9 dispatches in the first fixture run were left to arrive on their
        # own. Harmless there — the session never went idle — but as a subagent
        # that is precisely the state a completion notification wakes.
        self.assertIn(
            "Never end your turn holding an uncollected dispatch", self.orchestrator
        )

    def test_a_collected_agents_notification_is_a_no_op(self):
        self.assertIn("you have already collected is nothing", self.orchestrator)

    def test_the_turn_count_survives_being_woken(self):
        self.assertIn("being woken does not reset it", self.orchestrator)

    def test_subagents_are_named_with_their_plugin_prefix(self):
        # 46 dispatches failed as "Agent type 'navigator' not found" in the
        # measured cohort against 4 in the baseline; each cost an Opus turn.
        for name in ("harness:worker", "harness:verifier", "harness:navigator"):
            with self.subTest(agent=name):
                self.assertIn(name, self.orchestrator)

    def test_the_skill_and_the_orchestrator_agree_on_prefixes(self):
        skill = (ROOT / "skills/implement/SKILL.md").read_text()
        for name in ("harness:orchestrator", "harness:reviewer"):
            with self.subTest(agent=name):
                self.assertIn(name, skill)


if __name__ == "__main__":
    unittest.main()
