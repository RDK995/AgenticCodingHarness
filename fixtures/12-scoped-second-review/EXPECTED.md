# 12 — The correction stayed inside its finding

The negative pair to `11-correction-wandered`. The same project and the same
shape of cycle-1 correction, confined to the files the finding named, where the
correct behaviour is a **scoped** second review that passes — and a milestone
that reaches `DONE` without a coordinator being instantiated to say so.

## Why this fixture exists

Two rules meet here, both from the 2026-08-25 review-layer measurement, and both
are rules about what *not* to do:

**A second review reads the correction diff, not the milestone again.** Cycle-2
reviews cost $14-55 each on the project measured, and four of seven found
nothing above `OPTIONAL`. A harness that widens every time is safe and pays
cycle-1 prices forever, so `11` alone would teach exactly the wrong lesson: it
rewards widening, and nothing would notice a run that widened always.

**A passing review needs no orchestrator.** Coordinating review cost $494
against the reviewer's own $410, and six cycles instantiated a coordinator to
find there was nothing to route. The skill now invokes the reviewer, applies the
completion gate itself — count the per-criterion rows against the criteria,
confirm nothing above `OPTIONAL` remains — and records `DONE`. This is the
fixture where that path runs.

## Setup

The milestone is seeded at `Status: REVIEW` with `Review Cycles: 1`. Cycle 1
graded all three acceptance criteria `PASS` and raised one IMPORTANT finding
against `receipt/parse.py` and `tests/test_parse.py`: `"1.2.3"`, `"1.234"` and
`"1.23"` all returned 123, because the fractional part was stripped of separators
and truncated rather than checked. `requirements.md` requires that an unparseable
amount is an error rather than a zero or a skip.

The correction is correct and confined. It validates the fractional part, and
brings two tests with it — `"1.2.3"` and `"1.234"` — so the criterion the
finding rested on is now covered rather than asserted. `### Review` records both
changed files, both named by the finding, and a `Pre-correction:` ref — the
`M1 implementation` commit, which the setup substitutes. The ref is what a scoped
review is scoped to; without one there is no correction diff and the review must
read the whole milestone.

**The rest of the repository is genuinely correct**, and that is load-bearing:
there is nothing here for a widened review to find, so the only difference a
widened review makes is its bill.

- `python3 -m unittest discover -s tests` → 6 tests, `OK`.
- `python3 -m receipt receipt.txt` → `$19.99`, `$0.07`, `$5.00`,
  `TOTAL $25.06` — matching the criterion exactly.

**Three commits**, as in `11`: the correction diff has to be identifiable as its
own range, so `pre-correction/` holds the two files as cycle 1 reviewed them.

```bash
git init -q
git add .gitignore .harness receipt.txt && git commit -qm baseline

C=$(mktemp -d)                      # outside the repo: it must not be committed
cp receipt/parse.py tests/test_parse.py "$C"/
cp pre-correction/parse.py      receipt/parse.py
cp pre-correction/test_parse.py tests/test_parse.py
rm -rf pre-correction
git add -A && git commit -qm "M1 implementation"
sed -i '' "s/PRE_CORRECTION_SHA/$(git rev-parse HEAD)/" .harness/milestones.md

cp "$C"/parse.py      receipt/parse.py
cp "$C"/test_parse.py tests/test_parse.py
rm -rf "$C"
git add -A && git commit -qm "M1 cycle 1 correction (T4)"
```

## Command

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Bash Grep Glob Task Agent" \
  -p "/harness:implement"
```

## Expected outcome

**Mechanically checkable, in `.harness/milestones.md`:**

- `Status: DONE`.
- `### Review Cycles` is `1` — cycle 1's correction, and nothing since. The
  review that passes ends the loop and is not itself a cycle.
- All three acceptance criteria checked `[x]`.
- Cycle 2's entry under `### Review` records the verdict and the review tier.

**Mechanically checkable, in the run's subagents:**

- Exactly one `harness:reviewer` was invoked for this cycle.
- **No `harness:orchestrator` was invoked after it.** The review passed; there is
  nothing to route, and instantiating a coordinator to record a `PASS` is the
  cost this path exists to remove. The check is the presence or absence of the
  subagent in the session transcript, not a claim in the report.
- No file was written under `.harness/reviews/`. That directory carries a
  findings report so a fix cycle can be given its path; a `PASS` has no report to
  hand on.

**Requires reading the report:**

- The review says it was scoped to the correction diff, and why — both changed
  files are named by cycle 1's finding, so nothing falsifies "nothing else
  changed".
- The completion gate is applied and *shown* to be applied: three criteria in
  the milestone, three rows in the reviewer's table, no `BLOCKER` or `IMPORTANT`
  outstanding. A run that reports `DONE` without that arithmetic has reached the
  right answer by agreeing with the reviewer, which is the one thing this
  harness never does.

## Failure modes worth recognising

- **Instantiating an orchestrator to record the `PASS`.** The failure this
  fixture exists to catch, and it looks like diligence. Nothing is wrong with
  the result; the milestone simply cost a coordinator context to write one line
  a fresh reviewer had already justified.
- **Widening anyway.** Correct outcome, cycle-1 bill. Undetectable from
  `milestones.md` — it shows up only as a reviewer that read the whole milestone
  diff when the record said it did not have to. This is why `12` is run and not
  merely assumed.
- **Finding something.** The repository is correct, so a `CHANGES REQUIRED`
  verdict here is a false positive, and an expensive one: it is the second
  cycle, so the cap is now spent and the next thing that goes wrong escalates to
  a human on a milestone that was finished. `OPTIONAL` findings are fine and
  block nothing; anything graded above that is the failure.
- **Passing on the reviewer's say-so.** The gate is arithmetic on the
  per-criterion table, not deference to the verdict line. A `PASS` whose table
  omits a criterion must be treated as `CHANGES REQUIRED` — that is precisely
  the shape `01-requirement-violation` catches, and it must not be reintroduced
  by moving the gate into the skill.
- **Skipping cycle 2.** The corrections would then land unreviewed. The
  measurement that produced scoping also found a review of a single correction
  catching a real `BLOCKER` for $1.98 — corrections carry their own defects, and
  scoping is what makes reviewing them affordable, not a reason to stop.

## Its pair

`11-correction-wandered` is the positive: the same shape of correction, one file
outside the finding, and a review that must widen back to the whole milestone
and catch a broken entry point. Neither fixture means much alone.
