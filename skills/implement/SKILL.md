---
name: implement
description: Primary workflow entry point — reads agreed requirements, plans milestones, drives each milestone through implementation, testing, and fresh review until acceptance criteria are proven, then runs a final holistic review. Use when the user asks to implement, build, or continue work on agreed requirements via the harness.
---

Drive `.harness/requirements.md` to a fully implemented, reviewed, evidence-backed
result — one milestone at a time, and one phase of a milestone per invocation —
using the `harness:orchestrator` subagent to run each implementation and fix
phase, and invoking the `harness:reviewer` subagent yourself for every review.

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
        IF ### Review Cycles is already 2 and a BLOCKER or IMPORTANT
        finding recorded there is still open:
            the cap is spent. Do NOT invoke a reviewer — a third review is
            the thing the cap forbids, and it is checked here because here
            is where reviews are invoked.
            invoke harness:orchestrator to ESCALATE, saying the cap is
            spent and passing no report path. It sets BLOCKED and writes
            the escalation contract, and routes nothing.
            STOP — report the escalation contract to the human.

        invoke a FRESH harness:reviewer at the tier derived below, scoped
        per "What a second review sees" — you invoke it, not the
        orchestrator

        IF it returns PASS:
            apply the completion gate yourself — it is mechanical:
              - every acceptance criterion in the milestone entry has a row
                in the reviewer's per-criterion table, and every row is PASS
              - no BLOCKER or IMPORTANT finding remains
            IF either check fails: treat the verdict as CHANGES REQUIRED —
            a PASS that does not cover every criterion is the failure this
            gate exists for, not a formality
            otherwise:
              - check every acceptance criterion off as [x], against the
                reviewer's per-criterion row and nothing else. A milestone
                that is DONE with criteria still unchecked contradicts its
                own record, and the boxes are what a human reads first.
              - record the verdict and the review tier under ### Review
              - set Status: DONE
            Do NOT increment ### Review Cycles — a review that passes is
            the verdict that ends the loop, not a cycle. Only a review
            whose findings were routed and fixed counts, which is what
            makes the cap countable.
            Do NOT invoke the orchestrator. There is nothing to route, and
            instantiating a coordinator to find that out was six no-op
            invocations and $165 on the one project this was measured on.

        IF it returns CHANGES REQUIRED:
            write its report verbatim to .harness/reviews/M<n>-cycle<c>.md
            invoke a FRESH harness:orchestrator for ONE fix cycle, passing
            the PATH and not the report body (findings re-emitted into a
            prompt are the same defect task packets had before M4b)

            it returns the milestone at REVIEW or BLOCKED — never DONE

            IF it returns REVIEW without Review Cycles having increased,
            or with Review Cycles above 2:
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

## Invoking the reviewer

Every review is invoked from here, with a fresh context, and given only the inputs
`${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md` asks for — requirements, the milestone
and its acceptance criteria, the diff, relevant surrounding code, validation
results. Never implementation discussion, rationale, or any orchestrator's
justification.

**At no less than the highest tier that produced the work.** Read the tier
recorded against each task in the milestone entry, take the highest, and override
the reviewer's model to it:

```
highest tier used      reviewer runs at
Cheap  (haiku)    →    sonnet   (the reviewer's pinned floor)
Mid    (sonnet)   →    sonnet
Top    (opus)     →    opus
```

Never override the reviewer *downwards*: `sonnet` is the floor even for a
milestone that was entirely Cheap-tier work. A reviewer weaker than the work it
judges is the worst failure available to this system — it does not fail loudly, it
emits a confident, well-formatted per-criterion `PASS`, and the completion gate
then opens on nothing. Record the tier in `### Review` beside the verdict, so the
pairing is auditable rather than assumed.

## What a second review sees

A cycle-1 review reads the whole milestone. **A cycle-2 review reads the
correction diff**, plus the acceptance criteria those corrections touch. Nothing
else changed since cycle 1 graded it, and re-reading it costs cycle-1 money for a
verdict cycle 1 already gave.

Pass the reviewer the files the fix cycle recorded under `### Review` as its
correction diff, and say which criteria they bear on.

**Widen back to the whole milestone if the corrections changed a file no cycle-1
finding named.** The scope rests entirely on "nothing else changed", and a
correction that wandered outside its findings falsifies that. The fix cycle is
required to record such a file explicitly; if `### Review` does not say either way,
treat it as widened rather than assuming.

Do not skip the second review because cycle 1 found nothing serious. Corrections
carry their own defects: on the one project this has been measured, a review scoped
to a single correction cost **$1.98** and found a `BLOCKER` — a guard test that
asserted nothing — where full-scope cycle-2 reviews cost $14-55 each and four of
seven found nothing above `OPTIONAL`. Scope is what makes the second review worth
running; skipping it is not.

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
- final validation output (the broadest appropriate validation command for
  this repository), which it re-runs itself rather than crediting

**It is scoped to what no milestone review could see** — requirement coverage
across milestones, integration between them, and architectural drift — because
every milestone's own diff has already been reviewed at the tier that produced it,
and most of them twice. Its reading is bounded accordingly: the milestone records,
`drift.md`, the validation it runs, and whatever code a specific question sends it
to. **Do not hand it the complete project diff.** A whole-project diff at the top
tier is the largest single invocation this harness can make, and it re-reads work
that already carries a fresh reviewer's verdict.

Hand it the full diff only when a human asks for it — a release gate, a handover,
an audit. That is a deliberate, priced decision rather than the default.

> **This review has never run.** Across seven milestones of the one real project
> the harness has been measured on, no project has yet reached all-DONE, so the
> final review has no evidence behind it at all — neither for its cost nor for
> what it catches. The scope above is what the rest of the evidence supports, not
> a measured result. The first project that reaches this point should record what
> it cost and what it found.

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
