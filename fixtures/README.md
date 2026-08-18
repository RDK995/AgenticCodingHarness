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
git init -q && git add -A && git commit -qm baseline    # some fixtures need a diff
```

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
| `02-loop-cap` | Does contradictory work reach `BLOCKED` after exactly two cycles, instead of looping or faking a pass? | B11 |
| `03-drift-undeclared` | Is a silently dissolved component boundary caught **while every test passes**? | B13 |
| `04-drift-declared` | Is the same departure, once recorded, correctly *not* a finding? | B13 |
| `05-golden-path` | Baseline: does the whole workflow still work at all? | B8, B14 |

## Reading the results

The failure that matters is not a crash. It is a confident, well-formatted report
that says `PASS` when the answer is no.

`03` is the sharpest: every test passes and every acceptance criterion genuinely
holds, so nothing in the output hints that anything is wrong. An agent that
reports `PASS` there has not failed loudly — it has produced evidence that looks
exactly like success. Treat `01` and `03` as the two that decide whether a model
can hold the `reviewer` role at all; see `docs/runtime-contract.md` for why that
role is the one to protect.
