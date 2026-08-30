# 13 — Golden path, with an architecture

First validated in **B27 task 6**. `05-golden-path` runs the whole workflow from
a standing start but has no `architecture.md`, so it never triggers the as-built
path. This is the same baseline run *with* an agreed architecture: it is the only
fixture that exercises RECORD and COMPOSE **through the `implement` loop** rather
than by invoking `harness:as-built` directly.

`10-as-built-drift` tests what the as-built agent reports. This tests that the
loop calls it at all, in the right places, and does the right thing with what
comes back.

## Setup

Agreed requirements and an `AGREED` architecture with a `## Diagram`. No
`milestones.md`, no source. The harness plans, implements, reviews, records the
as-built, composes the comparison, and finally reviews — from nothing.

The architecture is deliberately two components with one edge
(`C2 CLI Entrypoint → C1 Conversion Function`), so that any as-built record it
produces is small enough to check by eye against the source.

**The architecture in this fixture was not hand-written.** It is the output of a
real `harness:architect` run against `requirements.md`, kept verbatim. That is
what makes it evidence for the `## Diagram` criterion rather than a diagram
written to match the rule it is supposed to test.

```bash
git init -q && git add -A && git commit -qm baseline
```

## Commands

Two invocations, exactly as `05` needs two — the LOOP stops at the milestone
boundary and hands back.

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Bash Grep Glob Task Agent" \
  -p "/harness:implement"
```

Then, in the same copy:

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Bash Grep Glob Task Agent" \
  -p "/harness:implement"
```

## Expected outcome

**Mechanically checkable:**

- `.harness/milestones.md` exists; every milestone reaches `Status: DONE`.
- `.harness/as-built/M<n>.md` exists for each `DONE` milestone, and its
  frontmatter-pinned tier is the Cheap one — the record is not written by the
  orchestrator's context.
- `.harness/as-built/drift.md` exists once every milestone is `DONE`.
- **`### As-Built` in the milestone record contains a path and a one-line
  result — never a diagram.** A Mermaid block in `milestones.md` is the failure
  this field exists to prevent: it makes every later session pay to read a
  picture it does not need.
- The test suite passes when re-run independently, outside the agent's session.

**Requires reading the report:**

- The final review runs at the top tier, is handed `drift.md`, and works the
  architecture question from it rather than re-deriving the graph from a
  project-wide diff.
- No orchestrator turn reads the contents of an as-built file. Check the
  transcript's `Read` calls, not the summary — the record carries a path
  precisely so this stays true, and a summary saying "recorded" proves nothing
  either way.

## What the first run actually did

All of the above held. Specifically:

| | Result |
| --- | --- |
| Milestones planned from nothing | 1 — one thin end-to-end slice, both components plus the seam |
| M1 | `DONE`, review `PASS` at `sonnet` (the floor for Cheap-tier work) |
| `.harness/as-built/M1.md` | written after `DONE`, both components observed **as claimed**, no claim mismatches |
| `### As-Built` field | path + one-line result, no diagram |
| `drift.md` | 2 components, 1 edge, all planned and built; nothing undeclared |
| Final review | `PASS` at `opus`, given `drift.md`, two `OPTIONAL` findings |

The as-built record correctly filed `test_temp_convert.py` under
`## Unmapped Files` — a test is not a component — rather than inventing a
component for it or silently dropping it.

## Failure modes worth recognising

- **A diagram pasted into `milestones.md`.** The whole cost argument for the
  as-built path is that the picture is written once and read by the reviewer,
  not carried in the coordinating context. A correct diagram in the wrong file
  is still a failure.
- **The as-built record echoing `### Architecture`.** If the milestone claims
  `C1, C2` and the record reports `C1, C2` without the files to back them, the
  agent has repeated a claim rather than made an observation. Check its
  `Components Observed` table cites real paths.
- **An invented `C<n>` for an unplanned component.** Those ids mean "agreed".
- **The final review re-deriving drift from a whole-project diff** when
  `drift.md` was supplied. That is the most expensive invocation the harness can
  make, and it is buying a comparison it was already handed.

## A contradiction this fixture surfaced

The run's final review returned `PASS` and **wrote nothing to `milestones.md`**.

That is correct per the current contract:
`skills/implement/references/milestones-template.md` says `## Final Review`
"exists only once every milestone is `DONE` **and the final review returned
findings**", and `SKILL.md`'s `IF the reviewer returns PASS` branch only says
"tell the user implementation is COMPLETE".

But `fixtures/05-golden-path/EXPECTED.md` requires the opposite — "recorded
under a `## Final Review` heading" — for a review that reports `COMPLETE`.

Both cannot be right. Recorded in `.harness-dev/progress.md` under B27's
follow-ups rather than resolved here, because resolving it changes the skill and
that is not what this fixture was written to test. Worth noting which way it
probably wants resolving: a passing final review is the most expensive
invocation in the system, and on the current contract its verdict and tier
survive only in the chat transcript — so a fresh session cannot tell whether the
project was ever finally reviewed. That is the state the harness's own
"conversation is not the source of truth" rule exists to prevent.
