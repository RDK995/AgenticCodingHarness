# `.harness/mvp.md` template

Write this file with these exact section headings, in this order.

```markdown
# MVP Scope

## Status

DRAFT | AGREED

## Full Scope

Requirements: .harness/full/requirements.md
Architecture: .harness/full/architecture.md | None — existing codebase

## Assumption

<one sentence, in a form that can turn out to be false>

Kind: technical | product | integration | performance

## Proof

Proven if: <observable result>
Not proven if: <observable result that would kill or change the approach>

## In Scope

| Full ref | What the MVP includes | Why the proof needs it |
| --- | --- | --- |

## Deferred

| Full ref | Comes back in | Why deferring is safe |
| --- | --- | --- |

## Components

| Id | Name | MVP | Note |
| --- | --- | --- | --- |
| C1 | <name> | IN \| STUBBED \| DEFERRED | <what the stub does, or why deferred> |

## Structural Commitments

### S1 — <the decision>

Taken at: full-scope fidelity
Reason: <what it would cost to change once a proven system rests on it>

## Expansion Path

### E1 — <name>

Adds: <full refs>
Needs from MVP: <what the MVP must not have precluded>

### E2 — <name>

...

## Decisions

<answers the human has given, and each increment promotion once it happens>
```

## Rules

- Set `## Status` to `AGREED` only after the human has explicitly agreed to the
  carve. Until then it is `DRAFT`, and `.harness/requirements.md` still holds the
  full scope.
- Every entry under the full requirements' `## Functional Requirements` appears
  exactly once, in `## In Scope` or in `## Deferred`. A requirement in neither is
  a scope decision nobody made.
- Every component in the full architecture appears in `## Components`, keeping its
  original id. Ids are never renumbered and a deferred id is never reused.
- Every row in `## Deferred` names an increment in `## Expansion Path`, and every
  increment names at least one deferred reference. Deferred work with no route
  back is cancelled work, and should be described as that instead.
- `## Proof` needs both lines. An MVP with no falsifying result cannot fail, and
  an MVP that cannot fail is not evidence.
- This file is a scope record, not a plan. It does not carry milestones, tasks,
  estimates or status for anything being built — `.harness/milestones.md` owns
  all of that, for the MVP and for every increment after it.
- Record a promotion under `## Decisions` when it happens, with the date and what
  the proof rested on. That line is why the next session can tell the difference
  between scope that was proven and scope that was assumed.
