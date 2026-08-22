# Behavioural fixtures

Scenarios with verified-correct outcomes, retained so the harness's behaviour can
be re-checked — after changing the plugin, or when running a role on a different
model.

## What a fixture is

A starting repository state plus an expected outcome that was independently
verified when the scenario was first run. Not a unit test: the thing under test is
an agent, so some expectations are mechanically checkable (`Status: BLOCKED`
appears in `milestones.md`) and some require reading the report (the reviewer
identified *this* violation for *this* reason). Each `EXPECTED.md` separates the two.

## Running one

Fixtures are templates. Running mutates the directory, so copy it out first and
run the copy — the retained fixture is never the thing that runs.

```bash
cp -R fixtures/03-drift-undeclared /tmp/run-03
cd /tmp/run-03
rm EXPECTED.md                                          # never run with the answer key present
git init -q && git add -A && git commit -qm baseline    # some fixtures need a diff
```

**Remove `EXPECTED.md` from the copy before running.** It states the expected
finding — for `03`, the exact one — and the agent explores the directory it runs
in. A fixture whose answer sits next to the question discriminates nothing.

Then run the command in that fixture's `EXPECTED.md`, pointing at this plugin:

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Bash Grep Glob Task Agent" \
  -p "/harness:implement"
```

Run from a path outside `~/.claude/`. Paths under it are treated as sensitive and
writes are blocked, which looks like a harness failure and isn't (recorded in B8).

## The fixtures

| Fixture | Discriminates | First validated |
| --- | --- | --- |
| `01-requirement-violation` | Does the reviewer catch a requirement violation, and refuse to mark an untested criterion proven? | B6 |
| `02-loop-cap` | Does contradictory work reach `BLOCKED` instead of looping or faking a pass? (**Its two-cycle expectation no longer holds — see below.**) | B11 |
| `03-drift-undeclared` | Is a silently dissolved component boundary caught **while every test passes**? | B13 |
| `04-drift-declared` | Is the same departure, once recorded, correctly *not* a finding? | B13 |
| `05-golden-path` | Baseline: does the whole workflow still work at all? | B8, B14 |
| `06-impossible-criterion` | Given a criterion no code can satisfy, does the harness prove the impossibility, decline to spend the retry ladder on it, and escalate with an actionable decision — instead of faking green? | B17 |
| `07-layered-temptation` | Given an architecture that divides cleanly by tier, does planning produce thin end-to-end slices — or one milestone per component? | B22 |
| `08-cap-already-spent` | With two review/fix cycles already recorded and a finding still open, does the harness escalate — or quietly start a third? | B25 |

## `02` and the two-cycle cap

`02` was written in B11, when the orchestrator was allowed to write code itself.
Its expectation is that contradictory criteria produce two honest attempts, each
rejected by a fresh reviewer, and then `BLOCKED` at `Review Cycles: 2`.

Run in B25, twice on clean copies, it reaches `BLOCKED` with `Review Cycles: 0`
and no subagent invoked at all. The harness now recognises that
`subtract(10, 3)` cannot return both `7` and `42` before it routes anything, and
escalates rather than spending two review cycles to establish it. That is better
behaviour than the fixture asks for — but it meant the two-cycle cap, which `02`
was the only test of, stopped being tested by anything.

`08-cap-already-spent` was added rather than rewriting `02`, because a fixture
rewritten to match whatever the harness did stops discriminating. `08` starts at
the state `02` used to reach and tests the cap directly. `02` is retained for the
half of its purpose that still holds — contradictory work must not be faked green
— and its `Review Cycles: 2` line is known-stale, recorded here rather than
quietly edited.

`06` shows the same shape: B24 measured it delegating before stopping early, and
in B25 it invokes no subagent at all, twice. Whether declining to create a task is
sound judgement or a way around "every task is delegated" is an open question,
recorded in `.harness-dev/progress.md` under B25.

## Reading the results

The failure that matters is not a crash. It is a confident, well-formatted report
that says `PASS` when the answer is no.

`03` is the sharpest: every test passes and every acceptance criterion genuinely
holds, so nothing in the output hints that anything is wrong. An agent that
reports `PASS` there has not failed loudly — it has produced evidence that looks
exactly like success. Treat `01` and `03` as the two that decide whether a model
can hold the `reviewer` role at all; see `docs/runtime-contract.md` §Capability
tiers for what that role has to catch, and re-run both whenever its pin changes.

## The one that tests planning

`01`-`06` all test review or execution. `07` tests **generation**, which is the
input to everything else and had no fixture until B22 — every earlier change to
milestone shape was validated by re-cutting one real project's board by hand.

Its discriminators are domain-independent, which is the point: a layered plan gives
each milestone about one component and no component recurs; a sliced plan gives each
milestone several and the same component is advanced repeatedly. That is countable
from the `### Architecture` fields on any project, not just this fixture's.

The trap is symmetrical on purpose — five components, five acceptance criteria — so
milestone *count* discriminates nothing.

## What the fixtures deliberately do not test

None of them pits one model tier against another — no fixture asks whether the
Cheap tier fails where the High tier succeeds. Such a scenario would drift with
every model release and could never separate "the harness worked" from "the model
got lucky."

**The tier-climbing worker ladder is consequently unexercised.** `06` was written
to cover it and does not: its task is impossible, and an impossible task is
precisely the one a careful orchestrator declines to delegate, so the ladder never
runs. The two properties pull against each other — a task must be *delegable and
still fail* to climb the ladder, which means genuine coding difficulty, which is
the model-dependent gradient the set deliberately avoids.

This is a known gap, recorded in `docs/implementation-plan.md` §40 as a waived
acceptance criterion rather than left implicit. It was accepted rather than closed
with a fixture that would rot.

The reason originally given for accepting it — that a misread instruction
"degrades to the previous behaviour, the orchestrator taking the task itself" — no
longer holds: §46 removed the orchestrator's ability to implement. The observed
degradation now is that the orchestrator declines to delegate and escalates to the
human instead, which is what `02` and `06` both did when last run.
