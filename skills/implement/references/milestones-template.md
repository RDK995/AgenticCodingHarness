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

## Rules

- No JSON state store, no hidden state — this file plus `requirements.md` must
  be enough for a new Claude session to understand project status.
- A milestone may only become `DONE` once its `Evidence` and `Validation`
  sections contain real implementation/test evidence, not a claim.
- `### Review Cycles` counts completed review/fix cycles for that milestone and
  is used to enforce the two-cycle cap.
- `### Follow-ups` records out-of-scope ideas surfaced while working the
  milestone. It is a record, not a task list — items there must not be
  implemented as part of this milestone.
- `### Architecture` lists the component ids from `.harness/architecture.md`
  that this milestone realises (e.g. `C1, C3`). Write `N/A` when the project has
  no `architecture.md` — the field is always present so there is only ever one
  milestone template to match.
