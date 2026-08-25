# `.harness/milestones.md` template

Each milestone uses this exact structure:

```markdown
# Milestones

## M1 — <Outcome>

Status: TODO

### Outcome

### Architecture

### As-Built

### Acceptance Criteria
- [ ]

### Baseline

### Evidence

### Validation

### Review

### Review Cycles
0

### Follow-ups
```

Repeat the `## M<n> — <Outcome>` block for each milestone.

## Valid milestone states

```
TODO
IN_PROGRESS
REVIEW
DONE
BLOCKED
```

## State transition

```
TODO → IN_PROGRESS → REVIEW → DONE
```

Use `BLOCKED` from any state whenever the milestone requires human intervention.

## Archiving settled milestones

On a long project this file accumulates the full evidence of every completed
milestone, and every session then pays to read all of it to find the one
milestone that is still open.

Once the file passes roughly **400 lines**, move the detail of **settled**
milestones into `.harness/archive/M<n>.md` — one file per milestone, content
unchanged. Leave in `milestones.md`:

```markdown
## M1 — <Outcome>

Status: DONE

### Outcome

<the outcome text, unchanged>

Detail: `.harness/archive/M1.md`
```

A milestone is **settled** when no further work will be done on it. That is
either of:

- it reached `DONE`; or
- a human explicitly closed it out short of `DONE`, and that decision is recorded
  in the milestone itself.

Both are archivable. Restricting archiving to `DONE` alone is what strands a
file: a milestone abandoned mid-flight keeps every line of its evidence forever,
and abandoned milestones are usually the largest, because they are the ones that
went wrong.

Rules for archiving:

- Never archive the active milestone, or any milestone that is `BLOCKED`.
- Never archive the **most recently settled** milestone. The milestone in
  progress most likely builds on it, so its detail is the most likely to be
  needed. This protection covers **exactly one** milestone.
- Recency is measured over **settled** milestones, not `DONE` ones. A `DONE`
  milestone that two later milestones have been settled since is no longer the
  predecessor of anything, and holding it back only makes every session read it.
  Measure by position in the run, not by whether the newer entries reached
  `DONE`.
- The protected milestone may itself be one settled short of `DONE`. Its detail
  is unlikely to be *useful*, but it is still the most recent thing the current
  work sits on top of, and protecting exactly one is simpler than reasoning about
  which kind of settlement earns it.
- Move content; never summarise or drop it. The evidence is the record of what
  was actually verified.
- Archiving moves bytes, so verify it moved them: record `wc -l` of
  `milestones.md` before and after and of the archive file written, and confirm
  they reconcile. State files have been lost to rewrites that were assumed to
  have worked.
- Below the threshold, archive nothing. A short project keeps every milestone
  here in full, matching the template above exactly.

An archived milestone is the one case where a milestone in this file does not
carry every template heading — the remaining headings are in its archive file.

## Rules

- No JSON state store, no hidden state — this file plus `requirements.md` (plus
  `.harness/archive/` once milestones have been archived, read on demand) must
  be enough for a new session to understand project status. `.harness/tasks/`
  and `.harness/reviews/` do not change that: task packets and review reports are
  scratch for a milestone in flight, written so neither is re-sent to every
  worker, verifier, retry or fix cycle that needs it. Nothing reads them to learn
  project status, and they carry no evidence — that lives here.
- A milestone may only become `DONE` once its `Evidence` and `Validation`
  sections contain real implementation/test evidence, not a claim.
- `### Evidence` records, per task, the tier it entered at, the named reason if
  that was not Cheap, and the outcome at each rung attempted. The tier alone shows
  what was chosen; the outcome is what shows whether the choice was right, and it
  is the only record from which a human can see routing drifting upward over time.
- `### Baseline` records the commit the milestone started from, and the branch
  (e.g. `8b81cf1 on m0-implementation`). The orchestrator writes it as its first
  act on the implementation phase. A later phase runs in a fresh context and
  computes the milestone's diff from it, so a milestone past `TODO` without a
  baseline cannot be reviewed. The harness does not commit after every task, so
  the milestone's work may be uncommitted or untracked: whoever records evidence
  says whether it is in `git diff <baseline>` or in `git status --porcelain`.
- `### Review` records each cycle's verdict, the tier it ran at, and — for a
  cycle that routed corrections — **the files those corrections changed**, calling
  out any file no finding named. The next review is scoped to that list, so a
  missing or approximate one silently widens or narrows what gets re-reviewed.
- `### Review Cycles` counts completed review/fix cycles for that milestone and
  is used to enforce the two-cycle cap. A cycle is a review **whose findings were
  routed and fixed**. A review that passes ends the loop and is not a cycle, so it
  does not increment this — a milestone corrected twice and then passed records
  `2`, not `3`. Counting passing reviews makes the cap unreachable. It is the only record of the count that
  survives between invocations, since each phase runs in its own context.
- `### Follow-ups` records out-of-scope ideas surfaced while working the
  milestone. It is a record, not a task list — items there must not be
  implemented as part of this milestone.
- `### As-Built` holds the path to this milestone's as-built record and the
  one-line result the `as-built` agent returned (e.g.
  `.harness/as-built/M2.md — RECORDED, 3 components, 1 claim mismatch`). It is
  written once, after the milestone reaches `DONE`. **A path, never a diagram** —
  the picture lives in the file, and copying it here would make every later
  session pay to read it. Write `N/A` when the project has no `architecture.md`.
- `### Architecture` lists the component ids from `.harness/architecture.md`
  that this milestone realises (e.g. `C1, C3`). Write `N/A` when the project has
  no `architecture.md` — the field is always present so there is only ever one
  milestone template to match.
