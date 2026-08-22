# `.harness/milestones.md` template

Each milestone uses this exact structure:

```markdown
# Milestones

## M1 — <Outcome>

Status: TODO

### Outcome

### Architecture

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

## Archiving completed milestones

On a long project this file accumulates the full evidence of every completed
milestone, and every session then pays to read all of it to find the one
milestone that is still open.

Once the file passes roughly **400 lines**, move the detail of completed
milestones into `.harness/archive/M<n>.md` — one file per milestone, content
unchanged. Leave in `milestones.md`:

```markdown
## M1 — <Outcome>

Status: DONE

### Outcome

<the outcome text, unchanged>

Detail: `.harness/archive/M1.md`
```

Rules for archiving:

- Never archive the active milestone, the most recently completed one, or any
  milestone that is `BLOCKED`.
- Move content; never summarise or drop it. The evidence is the record of what
  was actually verified.
- Below the threshold, archive nothing. A short project keeps every milestone
  here in full, matching the template above exactly.

An archived milestone is the one case where a milestone in this file does not
carry every template heading — the remaining headings are in its archive file.

## Rules

- No JSON state store, no hidden state — this file plus `requirements.md` (plus
  `.harness/archive/` once milestones have been archived, read on demand) must
  be enough for a new session to understand project status.
- A milestone may only become `DONE` once its `Evidence` and `Validation`
  sections contain real implementation/test evidence, not a claim.
- `### Baseline` records the commit the milestone started from, and the branch
  (e.g. `8b81cf1 on m0-implementation`). The orchestrator writes it as its first
  act on the implementation phase. A later phase runs in a fresh context and
  computes the milestone's diff from it, so a milestone past `TODO` without a
  baseline cannot be reviewed.
- `### Review Cycles` counts completed review/fix cycles for that milestone and
  is used to enforce the two-cycle cap. It is the only record of the count that
  survives between invocations, since each phase runs in its own context.
- `### Follow-ups` records out-of-scope ideas surfaced while working the
  milestone. It is a record, not a task list — items there must not be
  implemented as part of this milestone.
- `### Architecture` lists the component ids from `.harness/architecture.md`
  that this milestone realises (e.g. `C1, C3`). Write `N/A` when the project has
  no `architecture.md` — the field is always present so there is only ever one
  milestone template to match.
