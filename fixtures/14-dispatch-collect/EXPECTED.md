# 14 — The orchestrator collects what it dispatches

Specified 2026-09-09, from the field measurement of the same date. **Not yet run
against a live harness.**

Exercises the dispatch-and-collect rule: an orchestrator must block on
`TaskOutput` to collect a subagent's result rather than ending its turn to wait,
because a completion notification re-enters the context it already holds and
restarts its `maxTurns` allowance on it.

## Why this fixture exists

Measured across 24 field sessions: 84 orchestrator contexts produced 326
segments, **no segment over the 30-turn cap and one context at 147 turns**. The
cap was enforced perfectly inside every allowance and bounded nothing, because
each of 242 re-entries granted a fresh one. 53% of orchestrator traffic accrued
past cumulative turn 30.

The three acceptance criteria here are deliberately independent, so a correct run
dispatches several workers at once. That is the case the fix must not break:
blocking on collection must not serialise dispatch. 88% of measured orchestrator
contexts had two or more agents outstanding simultaneously.

## Setup

```bash
git init -q && git add -A && git commit -qm baseline
```

## Command

```bash
# One invocation per phase, as skills/implement/SKILL.md drives them.
for phase in 1 2 3 4 5; do
  claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
    --allowedTools "Read Write Edit Bash Grep Glob Task Agent" \
    --agent harness:orchestrator \
    -p "Run the next phase of milestone M1, per its Status in .harness/milestones.md."
  grep -qE '^Status: (DONE|BLOCKED)' .harness/milestones.md && break
done
```

## Expected outcome

**Mechanically checkable, in `.harness/milestones.md`:**

- `Status: DONE` with all three acceptance criteria ticked and evidence recorded.

**Mechanically checkable, in the run's transcripts.** Point
`.harness-dev/measure-context.py` at the session directory:

- `caps_evaded_by_re_entry` is **empty**. This is the fixture's point: a context
  over its cap whose longest segment is under it means the agent waited by
  ending its turn.
- Every orchestrator context reports `segments: 1`, or `2` where a trailing
  notification arrived after the work was already collected.
- `notification_re_entries` is at most one per orchestrator context.
- `polling_violations` attributable to the orchestrator is `0` — no `sleep`, no
  file polling, and no `Monitor` armed on a subagent's output.

**Requires reading the transcript:**

- Each dispatch is followed by a `TaskOutput` call carrying that agent's id with
  `block: true`, and the orchestrator does not end its turn between the two.
- Independent tasks were dispatched before any of them was collected, not one at
  a time. Three workers outstanding at once is the expected shape here; three
  dispatch-wait-dispatch cycles is the regression this fixture exists to catch.
- If a worker outran the ten-minute wait, `TaskOutput` was simply called again
  rather than replaced by a sleep or a Monitor.

## Failure modes worth recognising

**The one that looks like success:** every segment lands under 30 turns and the
per-invocation cap reports clean, while the context grows past it. Judge
`api_turns` against the cap, never `max_segment_turns` alone — that is exactly
the reading that hid this for a whole cohort.

Also watch for: serialised dispatch (correct results, one worker at a time, and
a phase that takes three times as long); a `Monitor` armed on a worker's evidence
file, which is the old waiting habit wearing a different hat; and a bare
`worker` or `navigator` in a dispatch, which fails as an unregistered agent type
and silently costs a turn.
