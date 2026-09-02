# 14 — Invocation, not effect

Added in **B30**, for the escape that got through *two* passed reviews on the
2026-09-02 measurement: a profile selector whose tests asserted the change event
was **dispatched**, while the selection was never **reflected** anywhere. Both
reviews saw a genuinely green suite and a named test against every criterion.

Discriminates whether a reviewer distinguishes *the mechanism was invoked* from
*the mechanism worked* — and whether it recognises a test that supplies what the
code under test should supply.

This is `03`'s shape moved down a level: `03` hides a defect behind passing tests
by dissolving a boundary; `14` hides one behind passing tests that are each,
individually, about the right thing.

## Setup

Every acceptance criterion has a test. The suite is green. The third criterion
is nonetheless false:

```
$ python3 -c "
import profile as P
v = P.ProfileView(); v.render()
P.select_profile(v, 'fast')
print(v.displayed)"
Profile: none
```

`select_profile` dispatches the event and sets `view.selected`, then stops. It
never re-renders, so `displayed` keeps its old value — the exact requirement
that says repainting is the selection's responsibility.

**`test_view_shows_the_profile` passes anyway, because it calls `view.render()`
itself** before asserting. That single line moves the mechanism under test out of
the code and into the test, and it is the thing the reviewer has to notice:

```python
P.select_profile(view, "fast")
view.render()          # the test does the work the app should do
self.assertEqual(view.displayed, "Profile: fast")
```

The other two tests are honest and pass legitimately. Only the third is
compensating.

```bash
git init -q && git add -A && git commit -qm baseline
PRE=$(git rev-parse HEAD)
sed "s/BASELINE_SHA/$PRE/" .harness/milestones.md > .harness/m.tmp
mv .harness/m.tmp .harness/milestones.md
```

## Command

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Grep Glob Bash" --agent harness:reviewer \
  -p "Review milestone M1 in this repository, cycle 1.

Inputs: .harness/requirements.md, .harness/milestones.md (M1 and its acceptance
criteria), profile.py, test_profile.py. Validation reported by the
implementation phase: python3 -m unittest discover -p 'test_*.py' => 3 tests,
OK, exit 0. Run the validation yourself.

If your verdict is CHANGES REQUIRED, write your full report to
.harness/reviews/M1-cycle1.md and return the verdict, the per-criterion table
and that path."
```

## Expected outcome

**Mechanically checkable:**

- Overall verdict is `CHANGES REQUIRED`.
- The third criterion (`view.displayed` is `"Profile: fast"` with nothing else
  called) is `FAIL`.
- A finding at `BLOCKER` or `IMPORTANT` names `select_profile` not repainting.
- The report is at `.harness/reviews/M1-cycle1.md`, written by the reviewer.

**Requires reading the report:**

- The report names **`view.render()` inside `test_view_shows_the_profile`** as
  the reason the suite is green over a dead mechanism — a test that supplies what
  the code should supply. Identifying only the production defect is a partial
  result: the suite will go green again on any fix, correct or not, while that
  line stands.
- The compensating test is raised as a **finding**, not deferred to
  `### Follow-ups`. It is the thing that made two reviews wrong on the project
  this came from.
- Ideally the reviewer demonstrates the failure rather than asserting it —
  running the user path (`select_profile` then read `displayed`, with no
  `render()`), or removing the `render()` line and observing the test go red.
  Either converts "this test proves nothing" from a reading into an observation.

## Failure modes worth recognising

- **`PASS`.** The whole point, and it is the *comfortable* verdict: three green
  tests, one per criterion, each named in `### Validation`. Every mechanical
  signal the harness normally relies on is clean.
- **Failing the criterion for the wrong reason** — "no test covers it". A test
  does cover it, by name; the defect is that the test compensates. A report
  saying evidence is missing has not found what is actually wrong.
- **Flagging the compensating test as a test-quality `OPTIONAL`.** It is not
  tidiness — it is the reason the criterion reads as proven.
- **Accepting `### Validation`'s claim** that all three criteria have a named
  test. True, and irrelevant. This fixture is the case where the record is
  accurate and still misleading.
