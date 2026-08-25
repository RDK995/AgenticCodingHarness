# 11 — A correction wandered outside the files its finding named

Exercises the scope of a **second** review: it reads the correction diff rather
than the whole milestone, and must widen back to the whole milestone when a
correction changed a file no cycle-1 finding named.

## Why this fixture exists

The 2026-08-25 review-layer measurement found that cycle-2 reviews cost
$14-55 each and that four of seven found nothing above `OPTIONAL`, while one
review scoped to a single correction cost **$1.98** and found a real `BLOCKER`.
Cycle 2 is now scoped to the correction diff and the criteria it bears on.

Scope is a saving with a hole in it. It rests entirely on "nothing else
changed", and a correction that edits a file outside its finding falsifies that
without announcing it. The rule is therefore that such a file widens the review
back to the whole milestone — and a rule nothing exercises is a rule that
decays. This is the fixture that exercises it.

## Setup

The milestone is seeded at `Status: REVIEW` with `Review Cycles: 1`. Cycle 1
raised one IMPORTANT finding against `receipt/parse.py` and `tests/test_parse.py`
— money held as a float — and graded AC2 and AC3 `PASS`, AC3 by running the
entry point.

The correction is **correct**, and correctly applied: amounts are now whole
cents, built by integer arithmetic. It also touched `receipt/total.py` and
`tests/test_total.py`, which no finding named, to drop a `round()` that no longer
means anything and to reword its assertion in cents. Both edits are harmless in
themselves — `receipt/total.py` is the one that matters, because a source file
outside the findings is what falsifies "nothing else changed".

What nobody touched is `receipt/report.py`, which formats what `parse_amount`
returns:

```python
out = ["$%.2f" % amount for amount in amounts]
```

Correct against dollars. Against cents it prints `$1999.00` for a `19.99` line.
**AC3 is now broken by a correction that never touched the file that broke.**

The state a run walks into:

- `python3 -m unittest discover -s tests` → 4 tests, `OK`. The suite covers AC1
  and AC2, both of which the correction genuinely improved.
- `python3 -m receipt receipt.txt` → `$1999.00`, `$7.00`, `$500.00`,
  `TOTAL $2506.00`, against the `$19.99 … TOTAL $25.06` the criterion names and
  the `### Validation` transcript records.
- Nothing in the test output hints that anything is wrong.

`### Review` records a `Pre-correction:` ref — the `M1 implementation` commit,
which the setup substitutes — the path of the correction patch, and the four
files the correction changed. It does **not** flag `receipt/total.py` as being
outside the findings. That omission is deliberate:
the record is written by an agent, the harness requires the call-out, and the
rule for a record that does not say either way is to treat the scope as widened
rather than assume it is narrow. This fixture is the case that rule is for.

**Three commits.** The baseline, the implementation, and the correction — the
correction diff has to be identifiable as its own range, because that is what a
scoped review is scoped to. `pre-correction/` holds the four files as cycle 1
reviewed them; the setup swaps them in for the implementation commit and the real
ones back for the correction commit, then deletes the directory.

```bash
git init -q
git add .gitignore .harness receipt.txt && git commit -qm baseline

C=$(mktemp -d)                      # outside the repo: it must not be committed
cp receipt/parse.py receipt/total.py tests/test_parse.py tests/test_total.py "$C"/
cp pre-correction/parse.py      receipt/parse.py
cp pre-correction/total.py      receipt/total.py
cp pre-correction/test_parse.py tests/test_parse.py
cp pre-correction/test_total.py tests/test_total.py
rm -rf pre-correction
git add -A && git commit -qm "M1 implementation"
PRE=$(git rev-parse HEAD)
sed "s/PRE_CORRECTION_SHA/$PRE/" .harness/milestones.md > .harness/m.tmp
mv .harness/m.tmp .harness/milestones.md      # portable: sed -i differs on BSD and GNU

cp "$C"/parse.py      receipt/parse.py
cp "$C"/total.py      receipt/total.py
cp "$C"/test_parse.py tests/test_parse.py
cp "$C"/test_total.py tests/test_total.py
rm -rf "$C"
git add -A && git commit -qm "M1 cycle 1 correction (T4)"

mkdir -p .harness/reviews                     # the patch the fix cycle would have written
git diff $PRE HEAD -- receipt tests > .harness/reviews/M1-cycle1.patch
```

`### Baseline` refers to the first of these. An empty third commit is the defect
to avoid: with no correction diff, a scoped review has nothing to be scoped to
and the fixture tests the wrong thing.

## Command

One invocation, through the skill: the milestone is at `REVIEW`, and reviews are
invoked by the skill rather than by the orchestrator.

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Bash Grep Glob Task Agent" \
  -p "/harness:implement"
```

## Expected outcome

**Mechanically checkable, in `.harness/milestones.md`:**

- Cycle 2's `### Review` entry grades AC3 **FAIL**, with `BLOCKER` or
  `IMPORTANT` severity, on **fresh** evidence — a CLI run from this cycle, not
  the transcript under `### Validation`. That transcript is correct, and it is
  from before the correction. This is the fixture; everything else is the loop
  behaving normally around it.
- `### Review Cycles` is `2` when the milestone finishes: cycle 1's correction
  and cycle 2's. A passing review ends the loop and is not a cycle.
- The milestone may legitimately reach `DONE`. Finding the defect is what is
  being tested, not stopping at it — the loop routes the finding, fixes it, and
  re-reviews, and a `DONE` reached that way is correct. `DONE` reached *without*
  a cycle-2 `FAIL` on AC3 is the failure.

**Mechanically checkable, in the run's subagents:**

- A `harness:reviewer` was invoked, and it ran `python3 -m receipt` itself.
  AC3's evidence cannot come from the recorded transcript: that transcript is
  from before the correction, and crediting it is the failure.

**Requires reading the report:**

- The finding names `receipt/report.py` formatting cents with a dollar format,
  and ties it to the correction's change of representation rather than
  presenting it as a pre-existing bug.
- The run says **why** AC3 was in scope at all — because `receipt/total.py` is
  outside the files cycle 1's finding named, which widens the review back to the
  whole milestone. A run that widened by habit, or reviewed everything because
  it always does, reaches the right answer without the rule that produced it,
  and will narrow wrongly on the next milestone.

Be precise about what catches this. Re-running the entry point is what surfaces
`$1999.00`; the widening rule is what puts AC3 in scope to be re-run. A review
scoped to the correction diff could also reach `receipt/report.py` by chasing
callers of the function it is reading, and one that does has done well. The
failure being tested is the review that never grades AC3 at all, or grades it
from the record.
- Severity is `BLOCKER` or `IMPORTANT`, not `OPTIONAL`. An acceptance criterion
  that no longer holds is not a nit.

## Failure modes worth recognising

- **`PASS` on the correction diff.** The failure this fixture exists to catch.
  The correction is genuinely good: it fixes the finding, the tests are green,
  and the new arithmetic is exact. A review that reads only the correction diff
  has every reason to pass it, and the milestone completes with a broken entry
  point.
- **Grading AC3 from the record.** `### Validation` holds a real, correct CLI
  transcript. It is stale. A review that re-reads it instead of re-running the
  command produces per-criterion evidence that is true of a repository that no
  longer exists.
- **Widening without noticing why.** A run that reviews the whole milestone
  every cycle will catch this and has learned nothing; the measurement that
  introduced scoping was about the cycles where widening buys nothing.
- **Blaming the correction.** T4 is not the defect. The correction did what its
  finding asked; `receipt/report.py` was never updated to match. A finding that
  asks for the correction to be reverted is worse than the defect.
- **Fixing it in the review.** The reviewer has no `Write` or `Edit`. A run that
  routes the fix and completes the milestone in this cycle has skipped the
  fresh review of its own correction — which is the next cycle's job, and the
  cap's.

## Its pair

`12-scoped-second-review` is the negative: the same project and the same shape
of correction, confined to the files its finding named, where the correct
behaviour is a **scoped** review that passes. Run both. One of them alone tests
either widening or scoping, and the harness has to do each in the right case.
