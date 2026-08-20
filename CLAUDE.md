# Coding Harness V1 — Implementation Instructions

## Purpose

This repository is implementing the Coding Harness described in:

`docs/implementation-plan.md`

Treat that document as the V1 specification.

Track implementation state in:

`.harness-dev/progress.md`

Do not use the conversation as the authoritative source of implementation state when the repository files can answer the question.

## Sources of Truth

Use this priority order:

1. `docs/implementation-plan.md` — required V1 behaviour and architecture
2. `.harness-dev/progress.md` — current build milestone, task, evidence, blockers, and next action (completed milestones: `.harness-dev/archive/B<n>.md`, read on demand only)
3. Repository code and configuration — actual implementation
4. Git diff/history — actual changes
5. Test/build/lint/type-check output — actual validation evidence
6. Agent summaries — useful context only, never proof of completion

Core rule:

**Never trust an agent's assertion that work is complete. Verify completion from requirements, code changes, tests, and evidence.**

## Build Milestones

Implement the harness in this order:

1. B1 — Plugin scaffold loads
2. B2 — Harness state templates exist
3. B3 — Engineering practices reference exists
4. B4 — Requirements roasting works
5. B5 — Worker handles bounded low-risk work
6. B6 — Reviewer performs independent evidence-based review
7. B7 — Orchestrator coordinates milestone execution
8. B8 — Implementation skill executes the workflow
9. B9 — Example harness state files exist
10. B10 — README documents the V1 workflow
11. B11 — End-to-end fixture validates the harness
12. B12 — Simplification pass is complete

Do not reorder milestones unless a concrete dependency makes the documented order impossible. Record any such decision in `.harness-dev/progress.md`.

## Operating Protocol

When asked to continue implementation:

1. Read `.harness-dev/progress.md`. It is bounded to the `Current` pointer, the milestone index, and the active milestone; it does not grow as milestones complete. Do not read `.harness-dev/archive/` to work out what to do next.
2. Identify the `Current` milestone and task.
3. Read only the sections of `docs/implementation-plan.md` needed for that milestone. Locate them (`grep -n '^# ' docs/implementation-plan.md`), then read that line range (`sed -n 'A,Bp'`). The file is ~1700 lines; do not read it whole.
4. Inspect the repository for existing conventions and current implementation state.
5. If the milestone is `TODO`, set it to `IN_PROGRESS`.
6. Break only the current milestone into a small set of bounded tasks.
7. Implement one coherent change at a time.
8. Run focused validation after meaningful changes.
9. Record actual validation output/evidence in `.harness-dev/progress.md`.
10. Review the milestone against every acceptance criterion.
11. Set the milestone to `REVIEW` before final milestone verification.
12. Mark acceptance criteria complete only when supported by implementation and/or test evidence.
13. Mark the milestone `DONE` only when its completion gate passes.
14. Move the completed milestone's section to `.harness-dev/archive/B<n>.md` unchanged, and update the milestone index and the `Current` section to the next milestone and its first task.
15. Stop at the milestone boundary, when explicitly asked to work on only one milestone, or when blocked. A finished milestone ends the session — see Context Discipline.

Do not generate detailed tasks for future milestones before they become current.

## Context Discipline

Cost grows with how long a context lives, not with how much work it does. Once a
session sits at 150k tokens, every later turn re-pays for that whole window, so a
marathon session costs several times what the same work costs across sessions
that end at milestone boundaries.

Three levers, in order of size.

### End the session at each milestone boundary

A completed milestone is a context boundary. When a milestone reaches `DONE`:

- record its evidence in `.harness-dev/progress.md`;
- move its section to `.harness-dev/archive/B<n>.md`;
- commit it (see Git Discipline);
- stop, and tell the human to `/clear` before the next milestone.

Do not carry a finished milestone's context into the next one. `progress.md` plus
the repository is enough to resume — that is what the file is for. If the
conversation holds something a fresh session would need, that is a gap in
`progress.md`: fix the file rather than keep the session alive to preserve it.

Do not begin a milestone you cannot finish in the context left. Stopping cleanly
with progress recorded costs less than compacting, and loses less.

### Delegate bounded work

For each task, ask the routing questions from `agents/orchestrator.md`: is it
clearly specified, bounded, low risk, and easy to verify?

- All effectively yes → delegate it to a subagent, giving it a task packet rather
  than the conversation history. It runs in a fresh context on a cheaper tier, and
  what it reads never enters yours.
- Otherwise → keep it. Architecture, security, ambiguous bugs, public interfaces,
  and cross-cutting changes stay with the agent holding the requirements.

Delegation is the default for bounded work, not an optimisation to remember when
context gets tight. It does not relax the core rule: never trust a delegated
result — verify it from the diff, the tests, and the evidence.

### Read in ranges, not whole files

Read what answers the question, not the file containing the answer.

- Specification: `grep -n` for the section heading, then `sed -n 'A,Bp'`.
- Archive: one milestone file, on demand. Never the directory.
- Search before reading: `grep -rn` beats opening candidates to find out.

Re-reading something already in context is free and is not the concern; pulling in
1700 lines to use 40 of them is.

## Milestone Completion Gate

A build milestone may become `DONE` only when all are true:

- required implementation is present;
- required validation has actually been run;
- validation passes, or any non-passing result is explicitly permitted by the specification;
- no blocking review issue remains;
- every acceptance criterion has recorded evidence.

A checked box without evidence is not sufficient.

## Progress Updates

After meaningful progress, update `.harness-dev/progress.md`.

At minimum keep these accurate:

- `## Current`
- the milestone index
- overall milestone count
- current milestone `Status`
- current milestone tasks
- acceptance criteria
- validation
- evidence
- decisions
- blockers

Do not report percentage-complete estimates.

Prefer observable measures such as:

- `4 / 12 build milestones DONE`
- `3 / 5 acceptance criteria proven`
- `6 / 8 E2E checks PASS`

## Task Sizing

For the current milestone only:

- prefer 3–7 bounded tasks;
- make each task independently understandable;
- avoid broad tasks such as “implement the harness”;
- do not create hundreds of microtasks;
- keep testing inside the milestone rather than as a later phase.

## Scope Control

Work not required by the current milestone, the implementation plan, or correctness must not be implemented.

If a potentially useful improvement is discovered:

- do not implement it opportunistically;
- record it under the current milestone's `Decisions` or `Follow-ups` equivalent if relevant;
- continue the current milestone.

Do not introduce new infrastructure unless the V1 specification requires it.

V1 intentionally avoids unnecessary workflow/runtime infrastructure.

## Validation

Discover and use validation commands supported by the repository.

Prefer this order where applicable:

1. focused test
2. module/package tests
3. type checking
4. lint
5. integration tests
6. build / broader appropriate suite

Do not run a full suite after every small edit when focused validation is available.

Before a milestone becomes `DONE`, run the broadest appropriate validation for that milestone.

Record the exact command and result.

## Git Discipline

Use the Git diff as implementation evidence.

Keep changes for the current milestone focused.

Where practical, make completed build milestones clean commit boundaries.

Do not mix unrelated refactors or future milestone work into the current milestone.

Before reviewing a milestone, inspect the milestone's effective diff and relevant surrounding code.

## Blocking and Escalation

Set the milestone to `BLOCKED` instead of looping indefinitely when:

- a material product/design decision is required;
- repository state prevents safe progress;
- required validation cannot be made meaningful without a human decision;
- the allowed review/fix loop has been exhausted.

Record:

- Problem
- Requirement / Milestone affected
- Attempts made
- Remaining issue
- Recommended decision

Do not keep trying alternative implementations indefinitely.

## Building the Fixture

Introduce the fixture progressively rather than waiting until the very end.

Use it when useful during:

- B4 to validate requirements roasting;
- B5 to validate worker delegation and Red → Green → Refactor;
- B6 to validate reviewer and evidence-gate behaviour;
- B7/B8 for integrated workflow behaviour;
- B11 for the complete eight-check E2E run.

Keep the fixture intentionally small.

## Simplification

B12 is a deletion-oriented pass.

Ask:

> What can be deleted while preserving the required behaviour?

Prefer removing:

- duplicated instructions;
- redundant prompts;
- redundant state;
- unnecessary configuration;
- duplicated engineering rules;
- behaviour already provided natively by Claude Code.

Do not add abstraction merely to make the implementation look more sophisticated.

## Starting Instruction

If no implementation work has begun, start with B1 only.

Implement B1, validate it, update `.harness-dev/progress.md`, and stop when B1 is `DONE` or `BLOCKED`.

Do not implement B2 opportunistically while completing B1.
