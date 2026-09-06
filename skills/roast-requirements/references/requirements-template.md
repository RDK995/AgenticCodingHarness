# `.harness/requirements.md` template

Write this file with these exact section headings, in this order. Leave a section
empty (just the heading) if it genuinely has nothing to say, but `Open Questions`
must be either a real list or the literal word `None`.

```markdown
# Requirements

## Goal

## Functional Requirements

## Acceptance Criteria

## Constraints

## Non-Goals

## Edge Cases

## Decisions / Clarifications

## Open Questions
```

## Rules

- Give every functional-requirement bullet a stable id in the form
  `- [FR1] ...`, `- [FR2] ...`. Never reuse or renumber an existing id. The
  implementation state maps these ids to owning milestones and the all-DONE
  gate compares the complete set against this document.
- Set `## Open Questions` to exactly `None` only when the requirements gate has
  passed (no unresolved question is likely to materially change the implementation).
- `## Decisions / Clarifications` records answers the human has already given,
  so a future session doesn't re-ask them.
- This is the only persisted requirements state. Do not create any additional
  JSON/YAML/database state alongside it.
