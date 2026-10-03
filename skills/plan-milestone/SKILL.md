---
name: plan-milestone
description: Plans the next milestone's work before any of it is built — sizes the milestone, breaks it into tasks, routes each to a tier and writes their task packets — then walks the human through the plan and records it as AGREED only once they say so. Use before /harness:implement on each milestone, or when the user asks to plan, review or change the plan for the next milestone.
---

Turn the next milestone in `.harness/state.json` into an agreed task plan at
`.harness/plans/M<n>.md`. Do not implement anything from this skill: its only
output is a plan a human has agreed, with the task packets it names.

`/harness:implement` will not start a milestone whose plan is not `AGREED`.

## Algorithm

```
Check what is already in your own context, before reading anything.

IF this session has already planned or implemented a milestone, or carries
substantial unrelated work:
    STOP — tell the human to /clear and re-invoke this skill.

Apply the same requirements and architecture gates as /harness:implement:
    .harness/requirements.md missing → tell them to run roast-requirements; STOP
    Open Questions != None → STOP and say what is unresolved
    .harness/architecture.md present and Status != AGREED → STOP

IF .harness/state.json is missing:
    STOP — tell them to run /harness:implement once; it writes the milestones
    this skill plans.

Run python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-state.py .harness/state.json
    --milestones .harness/milestones.md --requirements .harness/requirements.md
    and STOP on any error.

Find the first milestone that is not DONE.

IF none: STOP — every milestone is DONE; nothing to plan.
IF it is BLOCKED: STOP — report its escalation contract.
IF its status is not TODO: STOP — it is already under way on the plan it has;
    tell them to run /harness:implement.
IF its plan is AGREED: STOP — tell them to /clear and run /harness:implement.

IF it has no plan:
    invoke harness:orchestrator for the PLANNING phase of that milestone

    IF SPLIT: report the parts in one sentence and invoke a FRESH
        harness:orchestrator for the PLANNING phase of the first part.
        At most 2 splits in a row; past that, STOP and report.
    IF BLOCKED: STOP — report the escalation contract.
    IF anything other than PLANNED with a plan path, or a response cut off
        before it says so: the phase did not finish. Do not read a half-written
        plan as a draft; STOP and report it.

PRESENT the plan (see below), and ask whether to go ahead.

IF they agree:
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/agree-plan.py .harness/state.json <id>
        --milestones .harness/milestones.md --requirements .harness/requirements.md
    git add .harness && git commit -m "M<n>: task plan agreed"
    Tell them to /clear and run /harness:implement (or /harness:implement-loop,
    which runs this milestone and stops at the next one that needs a plan).
    STOP.

IF they want changes:
    invoke a FRESH harness:orchestrator for the PLANNING phase with the plan
    path and their words verbatim — not your paraphrase. Then PRESENT again.
    This repeats as often as they like; a plan is cheap to change now and
    expensive to change once workers have run it.

IF they edited the plan file themselves:
    the packets and structured state no longer match it. Invoke a FRESH
    harness:orchestrator for the PLANNING phase, saying the human edited the
    plan and the rest must be brought in line with it. Then PRESENT again.
```

## Presenting the plan

Read `.harness/plans/M<n>.md` — it is short and written for this. Do not read
the task packets, the source, or the diff: the plan is what is being agreed, and
anything only a packet explains is a gap in the plan to send back.

Explain it so someone who has not been inside the work can decide in a minute:

- **What this milestone will do**, in two or three sentences, and how they will
  be able to see it working.
- **The tasks, in order**, one line each in plain words. Say which are cheap
  routine work and which get a stronger, more expensive model, and why — a
  task routed to the top tier names a risk, and that risk is worth a sentence.
- **Anything they should weigh**: the plan's risks and open points, and a size
  signal if one was raised.

Then ask one question with three answers: go ahead as planned; change something
(and what); or stop here. Keep task ids, reason codes and file paths out of the
question — they are in the plan for anyone who wants them.

## Never

- Never set a plan `AGREED` without the human's explicit agreement in this
  conversation. Silence, a question, or "looks fine so far" is not agreement.
- Never write or edit the plan, a task packet or structured state yourself,
  apart from `agree-plan.py`. Every change goes through the orchestrator so the
  three stay consistent.
- Never run `/harness:implement`, or route a task to a worker, from this
  session.
- Never plan a milestone other than the next one. Later plans would be written
  against code that does not exist yet.
