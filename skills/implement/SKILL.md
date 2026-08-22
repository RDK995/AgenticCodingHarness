---
name: implement
description: Primary workflow entry point — reads agreed requirements, plans milestones, drives each milestone through implementation, testing, and fresh review until acceptance criteria are proven, then runs a final holistic review. Use when the user asks to implement, build, or continue work on agreed requirements via the harness.
---

Drive `.harness/requirements.md` to a fully implemented, reviewed, evidence-backed
result — one milestone at a time, and one phase of a milestone per invocation —
using the `harness:orchestrator` subagent to run each phase and the
`harness:reviewer` subagent for the final holistic review.

> Work not required to satisfy the current requirements or acceptance criteria
> must not be implemented unless necessary for correctness. If you notice
> something else worth doing, record it under that milestone's `### Follow-ups`
> — do not implement it.

## Algorithm

```
Read .harness/requirements.md

IF missing:
    tell the user to run the roast-requirements skill first
    STOP

IF Open Questions != None, or material ambiguity remains:
    STOP and tell the user what's unresolved

Read .harness/architecture.md

IF present AND Status != AGREED:
    STOP — the architecture is still DRAFT; tell the user to finish the
    architect skill and agree it

IF absent:
    proceed normally — architecture is optional, and its absence is expected
    when extending an existing codebase. Do not generate one; it needs human
    agreement, which is the architect skill's job.

Read .harness/milestones.md

IF missing:
    invoke harness:orchestrator to do reconnaissance and generate milestones

LOOP:
    find the first milestone that is not DONE

    IF none exists (all DONE):
        break out of LOOP

    IF it is BLOCKED:
        STOP — report the milestone's escalation contract to the human, do not
        skip ahead to a later milestone

    IF its Status is TODO or IN_PROGRESS:
        invoke harness:orchestrator for the IMPLEMENTATION phase
        (recon, size/shape check, task breakdown, routing by tier,
        Red→Green→Refactor, focused validation, evidence recording — see
        ${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md for what it does)

        it returns the milestone at REVIEW, or SPLIT, or BLOCKED

        IF SPLIT: continue the LOOP — it found the milestone oversized, split
        it in milestones.md, and implemented nothing. The loop now picks up
        the first part.

    WHILE its Status is REVIEW:
        invoke a FRESH harness:orchestrator for ONE review/fix cycle
        (fresh reviewer at the derived tier, findings routed as correction
        tasks, validation, Review Cycles incremented)

        it returns the milestone at DONE, REVIEW, or BLOCKED

        IF it returns REVIEW without Review Cycles having increased,
        or with Review Cycles already at 2:
            STOP — the cap is not being honoured and the loop would not
            terminate. Report it to the human as a harness defect.

    IF BLOCKED: STOP — report the escalation contract to the human
    (BLOCKED means it hit the 2-cycle review/fix cap with unresolved
    BLOCKER/IMPORTANT findings, or needs a human planning decision)

    otherwise: continue the LOOP
```

## One invocation per phase, not per milestone

Each `harness:orchestrator` invocation above is a **separate context**, and that
is the point rather than an implementation detail. Measured on a real four-criterion
milestone run as a single invocation, the review/fix phase was **62% of the
orchestrator's total cost** — 221 turns against 306 for everything before it —
because each review turn re-paid for the whole implementation phase sitting
underneath it in the same context.

`.harness/milestones.md` is the handoff. It is already required to be enough for a
new session to resume, so this costs nothing to maintain; it only requires that the
loop above actually re-invoke rather than let one context run on. Do not collapse
these back into one invocation to save a round trip — the round trip is cheap and
the context it discards is not.

## Final fresh review

Once every milestone is DONE, invoke harness:reviewer in **final review mode**
(see "Final review" in ${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md), **overridden to
the top tier** — it covers work from every tier, so it runs at the highest one —
with:

- the original requirements
- the agreed architecture (.harness/architecture.md), if the project has one
- all milestone outcomes (from .harness/milestones.md, and from
  `.harness/archive/M<n>.md` for any milestone whose detail has been archived)
- the complete implementation diff (project start → now)
- final validation output (the broadest appropriate validation command for
  this repository)

```
IF the reviewer returns PASS:
    tell the user implementation is COMPLETE

IF the reviewer returns CHANGES REQUIRED:
    invoke harness:orchestrator with the reviewer's findings to create a bounded
    correction task, implement it, and validate it, then request another fresh
    final review

    cap this at 2 cycles total, same as the per-milestone review/fix loop

    IF still CHANGES REQUIRED after 2 cycles:
        STOP — set overall status to BLOCKED and report the escalation
        contract to the human
```

## Never

- Never mark a milestone or the overall implementation complete because an
  agent (worker, orchestrator, or yourself) merely claims it's done. Completion
  requires the reviewer's evidence-based sign-off recorded in `.harness/milestones.md`.
- Never skip the requirements gate to "save time" — an unresolved material
  question left unblocked here becomes wasted or wrong implementation later.
- Never continue past a `BLOCKED` milestone to a later one. Milestones build on
  each other; skipping ahead defeats the point of ordering them.
- Never loop the review/fix cycle more than twice (per milestone, and again for
  the final review) — escalate to the human instead.
- Never let the implementation and an agreed `.harness/architecture.md` drift
  apart silently. By the end, the architecture must describe what was actually
  built — either because the code matches it, or because every departure is
  recorded under its `## Deviations`.
