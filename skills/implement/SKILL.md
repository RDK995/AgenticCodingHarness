---
name: implement
description: Primary workflow entry point — reads agreed requirements, plans milestones, drives each milestone through implementation, testing, and fresh review until acceptance criteria are proven, then runs a final holistic review. Use when the user asks to implement, build, or continue work on agreed requirements via the harness.
---

Drive `.harness/requirements.md` to a fully implemented, reviewed, evidence-backed
result — one milestone at a time — using the `harness:orchestrator` subagent to run
each milestone and the `harness:reviewer` subagent for the final holistic review.

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

    invoke harness:orchestrator to run that milestone to completion
    (recon, task breakdown, routing, Red→Green→Refactor, focused validation,
    fresh review, acceptance verification, evidence recording — see
    ${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md for what it does)

    the orchestrator returns the milestone as DONE or BLOCKED
    (BLOCKED means it hit the 2-cycle review/fix cap with unresolved
    BLOCKER/IMPORTANT findings)

    IF BLOCKED: STOP — report the escalation contract to the human

    otherwise: continue the LOOP
```

## Final fresh review

Once every milestone is DONE, invoke harness:reviewer in **final review mode**
(see "Final review" in ${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md) with:

- the original requirements
- all milestone outcomes (from .harness/milestones.md)
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
