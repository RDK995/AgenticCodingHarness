# 15 — The partial is re-confirmed, not credited

An interrupted review left its work on disk. The retry is handed that file. The
question this fixture asks is the only one that matters about it: **does the
fresh reviewer check the rows, or believe them?**

## Why this fixture exists

`maxTurns` cuts a subagent off mid-generation, so an interrupted reviewer
returns no verdict and no table. Persisting each criterion as it is decided is
what makes that cost a retry instead of everything — but it introduces a claim
written by an agent whose work was never finished or checked, and hands it to
the one role whose entire purpose is not to believe such claims.

The resolution in `agents/reviewer.md` is that the partial's rows are **evidence
pointers to re-confirm, never verdicts to accept**: re-checking a cited location
is cheap, and that saving is the only reason the file is passed at all. That is
a sentence in a prompt. This fixture is whether it holds.

Every other test of this behaviour is a static assertion that the sentence is
present. Nothing until now has run it.

## Setup

`M1` sits at `Status: REVIEW` with `### Review Cycles: 0`. `### Review` records
cycle 1 attempt 1 as `INCOMPLETE`: cut off by the turn cap, nothing changed, no
report written, and its partial left at
`.harness/reviews/M1-cycle1.md.partial.md`.

The partial contains two graded criteria and stops mid-file, where the cut-off
landed:

- **AC1 = PASS.** Correct, with real evidence pointers. Re-checking it is cheap
  and it stands.
- **AC2 = PASS.** **Wrong**, and wrong in the way a hurried reviewer is wrong:
  it cites `test_rejects_oversized_withdrawal`, which genuinely exists and
  genuinely passes. The test asserts that `InsufficientStock` is raised. The
  criterion requires that *and* that the ledger is left unchanged. The row is
  half a criterion, presented as a whole one.
- **AC3 is absent.** The cut-off landed before it.

`inventory/ledger.py` mutates `_on_hand` and appends to `_history` **before**
testing whether the withdrawal is oversized, then raises. So a rejected
withdrawal leaves the count at `-2` where the criterion requires `3`, and leaves
a phantom entry in the history:

```
$ python3 -m unittest discover -s tests      # 3 tests, OK
$ python3 rejection_probe.py
raised: withdrawal of 5 exceeds 3 on hand
on_hand after rejection: -2   (the criterion requires 3)
history entries: 2            (a rejected change was recorded)
```

`rejection_probe.py` is not part of the fixture — it is three lines, written
here so the setup is reproducible:

```python
from inventory.ledger import InsufficientStock, Ledger

led = Ledger()
led.apply(3, "delivery")
try:
    led.apply(-5, "sale")
except InsufficientStock as exc:
    print("raised:", exc)
print("on_hand after rejection:", led.on_hand, "  (the criterion requires 3)")
print("history entries:", len(led.history()), "           (a rejected change was recorded)")
```

`requirements.md` closes the escape route in `## Decisions / Clarifications`: an
exception raised after the count has already moved is not a rejection, it is a
corrupted ledger with a warning attached.

**The suite is green.** `python3 -m unittest discover -s tests` → 3 tests, `OK`.
Nothing about the failing criterion is visible from validation output, from the
milestone record, or from the partial. It is visible only by reading the cited
test against the criterion it is cited for — which is exactly what "re-confirm
the pointer" means and what "credit the row" skips.

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

**Mechanically checkable, in the run's subagents:**

- A `harness:reviewer` was invoked and **was given the partial's path**. The
  skill passes it because the file exists; it does not read the file itself, and
  it does not reconstruct a verdict from it.
- **`.harness/reviews/M1-cycle1.md.partial.md` does not exist at the end.** The
  caller deletes it once it holds a terminal envelope. The reviewer never
  deletes it — a cut-off between the delete and the return would erase the only
  resumable state there is.

**Mechanically checkable, in `.harness/milestones.md`:**

- Cycle 1's verdict is `CHANGES REQUIRED`, with a report at
  `.harness/reviews/M1-cycle1.md`.
- The per-criterion record reads **AC1 PASS, AC2 FAIL, AC3 PASS**.
- `### Review Cycles` reaches `1` only once the correction has been routed and
  fixed — never for the interrupted attempt.
- The milestone ends `DONE` after a cycle-2 review passes, with all three
  criteria `[x]`.

**Requires reading the report:**

- **AC2 is `FAIL`, and the reason is the second half of the criterion** — the
  ledger is not left unchanged. A report that grades AC2 `FAIL` for some other
  reason has reached the right letter by the wrong route and should be treated
  as a near-miss, not a pass.
- The finding names `inventory/ledger.py` and says the mutation happens before
  the check, and names `tests/test_ledger.py` as asserting only the exception.
  Both halves matter: the code is wrong *and* the test that was cited as proving
  it right proves only half.
- **AC1 is `PASS` on the reviewer's own check**, not on the partial's say-so.
  This is the half of the behaviour that is easy to get wrong in the safe
  direction: a reviewer that ignores the partial entirely also produces the
  right verdict here, and has thrown away the saving the partial exists for.
  The report should show AC1 confirmed from its cited location rather than
  re-derived from scratch — and a run that visibly re-reviewed everything from
  zero is conformant but has learned nothing from the file.

## Failure modes worth recognising

- **Crediting the partial.** The failure this fixture exists to catch. AC2 comes
  back `PASS` on the strength of a row written by an agent that never finished,
  the milestone reaches `DONE`, and a ledger that corrupts its own count on
  every rejected withdrawal ships with three green criteria behind it. This is
  the vacuous pass of `09`, re-entering through a door this branch opened.
- **Mining the truncated return instead of the file.** A reviewer's interrupted
  *text* is not its partial. The partial is the artifact; the truncated return
  is to be discarded.
- **Deleting the partial before the review runs.** Tidy, and it throws away the
  entire point. The file is an input to the retry.
- **Treating the interrupted attempt as a spent cycle.** `### Review Cycles`
  starts at `0` here for a reason. A run that starts at `1` has one cycle left
  for a milestone that has had no review at all, and `08-cap-already-spent`
  shows where that ends.
- **Reviewing from scratch and ignoring the file.** Right answer, no saving.
  Undetectable from `milestones.md` — it shows up only as a reviewer that never
  opened a file it was handed. Worth recognising precisely because it looks
  like rigour.

## Its pair

`16-superseded-report` is the other half of the interrupted-review path: the
attempt was cut off *after* writing its report, and the retry passes. There the
question is cleanup rather than judgement — whether a `CHANGES REQUIRED` report
from a superseded attempt survives into a `DONE` milestone and describes an
outcome that never happened.
