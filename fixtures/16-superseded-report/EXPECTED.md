# 16 — The superseded report does not survive the review that replaced it

The cut-off can land *after* the reviewer writes its report and before it
returns. A `CHANGES REQUIRED` report is then sitting on disk with no envelope
behind it. The retry re-reviews and passes — and a passing review writes
nothing, so nothing overwrites the file.

The question: **does that report get committed with the `DONE` milestone,
describing an outcome that never happened?**

## Why this fixture exists

The rule that reports are the reviewer's artifact and the caller never writes
them is load-bearing everywhere else in the harness. It has one consequence
nobody had traced: on a `PASS`, the reviewer writes nothing, so the caller's
cleanup is the *only* thing that can remove a file a superseded attempt left
behind.

`15-partial-not-credited` asks whether the retry judges correctly. This one
asks whether the retry cleans up after the attempt it replaced. They are the
two halves of the interrupted-review path, and the second is the one that
silently corrupts the record rather than the code.

## Setup

`M1` sits at `Status: REVIEW` with `### Review Cycles: 0`. `### Review` records
cycle 1 attempt 1 as `INCOMPLETE`, with the cut-off landing after the report was
written. Two files are on disk from it:

- `.harness/reviews/M1-cycle1.md` — a complete `CHANGES REQUIRED` report.
- `.harness/reviews/M1-cycle1.md.partial.md` — its partial.

**The report's finding is a false positive, and its own Evidence line shows
why.** It raises IMPORTANT against AC2: the criterion requires a rejected
withdrawal to leave `on_hand` and `history()` unchanged, and it reports that no
test asserts that half. Its evidence cites `tests/test_ledger.py` — the only
test file it opened. `tests/test_rejection.py` exists, contains
`test_on_hand_is_unchanged_by_a_rejected_withdrawal` and
`test_history_records_nothing_for_a_rejected_withdrawal`, and asserts exactly
the half the finding says is unasserted.

That is not a contrived error. It is the characteristic error of a reviewer
about to run out of turns: it read one file where two were needed. The
interrupted return and the wrong finding have the same cause, which is why a
report with no envelope behind it earns no deference.

**The code is correct.** `inventory/ledger.py` runs the guard before any
mutation, so a rejected withdrawal leaves the ledger indistinguishable from one
where the call never happened.

- `python3 -m unittest discover -s tests` → 5 tests, `OK`.

```bash
git init -q
git add -A && git commit -qm baseline
BASE=$(git rev-parse HEAD)
git checkout -qb m1-ledger

sed -e "s/BASELINE_SHA/$BASE/" .harness/milestones.md > .harness/m.tmp
mv .harness/m.tmp .harness/milestones.md   # portable: sed -i differs on BSD and GNU
git add -A && git commit -qm "M1 implementation"
```

## Command

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Bash Grep Glob Task Agent" \
  -p "/harness:implement"
```

## Expected outcome

**Mechanically checkable, in `.harness/reviews/`:**

- **`M1-cycle1.md` does not exist at the end.** This is the fixture. A passing
  review writes no report, so the only file that can be at that path is the
  superseded attempt's, and the accepted-`PASS` path removes it.
- **`M1-cycle1.md.partial.md` does not exist at the end**, removed by the same
  cleanup on the terminal envelope.
- The directory itself may remain; it is the files that must not.

**Mechanically checkable, in `.harness/milestones.md`:**

- `Status: DONE`, all three criteria `[x]`.
- **`### Review Cycles` is `0`.** No cycle ever completed here: the interrupted
  attempt routed nothing, and the review that passed ended the loop rather than
  being a cycle. A run recording `1` has counted a review whose findings were
  never routed, which is the arithmetic `08-cap-already-spent` depends on.
- The `### Review` entry records the passing verdict and its tier.

**Mechanically checkable, in git:**

- No commit contains `.harness/reviews/M1-cycle1.md`. A run that removes the
  file only after committing it has recorded the false verdict permanently and
  then tidied the working tree, which is the failure with an extra step.
- `git status --porcelain` is empty at the end.

**Requires reading the report:**

- Nothing. There is no report — that is the expected outcome. The reviewer's
  returned envelope carries `Report: NONE`, `Result: PASS`, and a per-criterion
  line with all three `PASS`.
- The run's own record should say the superseded report was removed and why. A
  cleanup that happens silently is correct behaviour with no evidence behind it,
  and the next person to wonder where the report went has to reconstruct this.

## Failure modes worth recognising

- **The stale report survives to `DONE`.** The failure this fixture exists to
  catch. Everything looks right: milestone `DONE`, criteria checked, tests
  green — and `.harness/reviews/M1-cycle1.md` says the milestone required
  changes. Whichever a reader believes, the record contradicts itself, and the
  contradiction was introduced by the machinery meant to make interruption
  recoverable.
- **Deferring to the report instead of re-reviewing.** A complete report is a
  persuasive artifact. It has no envelope behind it, so it is not a review, and
  the completion gate has nothing to consume from it. A run that routes a
  correction for its false finding has spent a fix cycle answering an agent that
  never finished a sentence.
- **Deleting the report and treating the review as done.** The opposite error:
  the file is gone and no review has happened. The retry must actually run.
- **Refusing to delete anything under `.harness/reviews/`.** Defensible as a
  general instinct — reports are evidence — and wrong here for one specific
  reason: on a `PASS` the reviewer writes no report, so a file at that path
  cannot be the review that just happened.

## Its pair

`15-partial-not-credited` — the same interrupted-review path, where the cut-off
landed before the report and the partial contains a row that is wrong. There the
question is whether the retry re-confirms rather than credits. Neither fixture
means much alone.
