# `.harness/mvp.md` template

Write this file with these exact section headings, in this order.

```markdown
# MVP Scope

## Status

DRAFT | AGREED

## Full Scope

Requirements: .harness/full/requirements.md
Architecture: .harness/full/architecture.md | None — existing codebase

## Outcome

A <specific user> can <complete outcome> through <the real entry point>.

First user: <who gets it first>
Replaces: <what they do today, or do without>

## Value

Delivered when: <the outcome, observable through the real entry point>
Not delivered if: <a result that leaves the user still doing what this replaces>

## In Scope

| Full ref | What the MVP includes | Why the outcome needs it |
| --- | --- | --- |

## Deferred

| Full ref | Comes back in | Why deferring is safe |
| --- | --- | --- |

## Manual Steps

| Step | Who does it | Automated by |
| --- | --- | --- |

## Components

| Id | Name | MVP | Note |
| --- | --- | --- | --- |
| C1 | <name> | IN \| STUBBED \| DEFERRED | <what the stub does, or why deferred> |

## Structural Commitments

### S1 — <the decision>

Taken at: full-scope fidelity
Reason: <what it would cost to change once real users and real data rest on it>

## Expansion Path

### E1 — <name>

Adds: <full refs>
Needs from MVP: <what the MVP must not have precluded>

### E2 — <name>

...

## Decisions

<answers the human gave while scoping, and each increment promotion once it happens>
```

## Rules

- Set `## Status` to `AGREED` only after the human has explicitly agreed to the
  carve. Until then it is `DRAFT`, and `.harness/requirements.md` still holds the
  full scope.
- `## Outcome` names one user and one outcome. Two outcomes means the carve has
  not been made yet; serving several users thinly produces something neither
  small nor usable.
- Every entry under the full requirements' `## Functional Requirements` appears
  exactly once, in `## In Scope` or in `## Deferred`. A requirement in neither is
  a scope decision nobody made.
- Every component in the full architecture appears in `## Components`, keeping its
  original id. Ids are never renumbered and a deferred id is never reused.
- Every row in `## Deferred` names an increment in `## Expansion Path`, and every
  increment names at least one deferred reference. Deferred work with no route
  back is cancelled work, and should be described as that instead.
- `## Manual Steps` is empty only if a person does nothing the full scope would
  automate. Each row names the increment that automates it, and that increment
  appears in `## Expansion Path` like any other deferred work.
- `## Value` needs both lines. `Delivered when` and `the tests pass` are different
  claims, and only the first one is the reason to build an MVP.
- This file is a scope record, not a plan. It does not carry milestones, tasks,
  estimates or status for anything being built — `.harness/milestones.md` owns
  all of that, for the MVP and for every increment after it.
- Record a promotion under `## Decisions` when it happens, with the date and what
  prompted it. If use of the MVP reordered `## Expansion Path`, that reason is the
  most valuable line in the file: it is what building the small version first
  bought.
