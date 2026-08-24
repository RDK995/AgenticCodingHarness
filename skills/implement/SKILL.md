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
Check what is already in your own context, before reading anything.

IF this session has already driven a milestone to DONE, or carries
substantial work unrelated to the milestone about to run:
    STOP — tell the human to /clear and re-invoke this skill.
    Do not read requirements, architecture or milestones first:
    those reads, and every dispatch after them, are exactly what
    a carried context makes you pay twice for. See "And one
    session per milestone" below.

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

        it returns the milestone at REVIEW, or SPLIT, or CONTINUE, or BLOCKED

        IF SPLIT: continue the LOOP — it found the milestone oversized, split
        it in milestones.md, and implemented nothing. The loop now picks up
        the first part.

        IF CONTINUE: the phase is unfinished and the orchestrator handed off
        at its context ceiling, having recorded what it completed in
        milestones.md. Invoke a FRESH harness:orchestrator for the SAME phase.
        Cap this at 3 continuations per phase; past that, STOP and report to
        the human that the milestone does not fit its phase budget and needs
        splitting.

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

    otherwise:
        IF .harness/architecture.md exists:
            invoke harness:as-built in RECORD mode for this milestone,
            passing its number, its ### Baseline, and its ### Architecture
            field — it writes .harness/as-built/M<n>.md itself

            write its returned path and one-line result into the
            milestone's ### As-Built field. Do not read the file.

            IF it returns BLOCKED: record that in ### As-Built and carry on.
            The record is evidence, not a gate.

        the milestone is DONE — STOP HERE, in this invocation.
        Report its outcome and tell the user to /clear and re-invoke this
        skill for the next milestone. Do not continue the LOOP in this
        context. The LOOP is re-entered from milestones.md on the next
        invocation and picks up where this one stopped.
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

## And one session per milestone, not per project

The same argument applies one level up, to **your own** context. You are the
session running this skill, and nothing about a finished milestone helps you
run the next one — `milestones.md` already carries everything that does.

Measured on a real run of two consecutive milestones in one session: the session
grew from 33k to 171k tokens across 13 hours and 194 turns, and never compacted.
By the time the second milestone started, this skill's own context was **161k
tokens on average per turn** — for 24 turns that did nothing but dispatch phases
and read their returns. A fresh session starts that same work at roughly 35k.
The second milestone paid about three times what it needed to, for history
belonging to the first.

So the LOOP stops at each milestone boundary and hands back to the human. Tell
them to `/clear` before re-invoking. This is not a limitation to work around by
carrying on anyway: the milestone boundary is the cheapest context boundary in
the system, and it is free precisely because the state file is already required
to survive it.

**And it is checked on the way in, not only on the way out.** Stated only as an
exit instruction, this rule lost to a session that simply never ended. Measured on
the M5a run: the implementation phase was dispatched from a session opened 22 hours
earlier and already carrying 276k tokens, and its 49 turns cost $11.96. The review
cycle that followed it did the same 49 turns from a fresh session at 34k and cost
$2.57 — identical work, 4.6 times the price, all of it for history belonging to
other milestones. The Algorithm therefore opens by checking its own context and
refusing to start, because the human who has to act on the instruction is not the
one who reads it.

The check is provenance, not a token count: a session cannot reliably measure its
own size, but it can see whether it has already done a milestone's work. That is
the condition that actually failed, so that is the condition to test.

## Compose the drift comparison

Once every milestone is DONE and the project has an `.harness/architecture.md`,
invoke `harness:as-built` once more in **COMPOSE** mode. It unions every
`.harness/as-built/M<n>.md` into the system as actually built, lays it against the
agreed `## Diagram` and `## Components`, and writes `.harness/as-built/drift.md`.

Pass its path to the final review below. Do not read it yourself — the reviewer
is the context that needs it, and routing a full comparison through this one buys
nothing.

Skip this entirely when the project has no architecture. There is nothing to
compare against, and the harness's V1 behaviour is unchanged in that case.

## Final fresh review

Once every milestone is DONE, invoke harness:reviewer in **final review mode**
(see "Final review" in ${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md), **overridden to
the top tier** — it covers work from every tier, so it runs at the highest one —
with:

- the original requirements
- the agreed architecture (.harness/architecture.md), if the project has one
- the drift comparison (.harness/as-built/drift.md), if one was composed
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
- Never copy an as-built diagram into `.harness/milestones.md` or into your own
  report. The milestone record carries a path; the diagram stays in its file. A
  diagram pasted into shared state is re-read by every session that follows.
- Never let the implementation and an agreed `.harness/architecture.md` drift
  apart silently. By the end, the architecture must describe what was actually
  built — either because the code matches it, or because every departure is
  recorded under its `## Deviations`.
