---
name: plan-milestone
description: Creates the project's milestones from the agreed requirements (when they do not exist yet), then plans upcoming milestones' work before any of it is built — for each, sizes it, breaks it into tasks, routes each to a tier and writes their task packets — then walks the human through the plans and records them as AGREED only once they say so, so /harness:implement-loop can run through all of them. Use before /harness:implement or /harness:implement-loop, or when the user asks to plan, review or change the plans for coming milestones. Optional argument: --until <milestone-id> (plan up to and including it) or --next <n>.
---

Create the project's milestones if there are none yet, then turn the upcoming
ones into agreed task plans at `.harness/plans/M<n>.md`. Do not implement
anything from this skill: its only output is the milestones and plans a human
has agreed, with the task packets they name.

`/harness:implement` will not start a milestone whose plan is not `AGREED`, and
`/harness:implement-loop` stops at the first one. Plan as far ahead as the human
wants the loop to run unattended.

## Algorithm

```
Check what is already in your own context, before reading anything.

IF this session has already implemented a milestone, or carries substantial
unrelated work:
    STOP — tell the human to /clear and re-invoke this skill.

Apply the same requirements and architecture gates as /harness:implement:
    .harness/requirements.md missing → tell them to run roast-requirements; STOP
    Open Questions != None → STOP and say what is unresolved
    .harness/architecture.md present and Status != AGREED → STOP

IF .harness/state.json is missing but .harness/milestones.md exists:
    an older harness wrote it. Run python3
    ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-state.py .harness/milestones.md
    .harness/state.json --requirements .harness/requirements.md once. If it
    reports ambiguous ownership, STOP and ask the human for the explicit
    id-to-milestone JSON map required by --ownership; never guess ownership.
    STOP on any migration error rather than guessing.

IF neither exists — CREATE THE MILESTONES:
    open the plans branch (BRANCH below) first, so the milestones are
    committed there too.
    invoke a FRESH harness:orchestrator to do reconnaissance and generate
    milestones.
    IF it returns BLOCKED: STOP and report. Generation does not hand off — a
        milestones.md covering half the requirements is indistinguishable
        downstream from a complete one, so the orchestrator writes the
        milestones in full or writes nothing, and the recon it recorded is
        what the next attempt starts from.
    Confirm both files exist, every template heading is present, and
    check-state.py (below) passes.
    PRESENT THE MILESTONES: one line each, in order, in plain words — what
    the project can do once it is done, and how anyone could see it working.
    Ask whether the split looks right before any task planning: a wrong cut
    is cheap to fix now and costs every plan written on top of it.
    IF they want changes: invoke a FRESH harness:orchestrator to revise the
        milestones, with their words verbatim. It rewrites both files in
        full. Then present again.
    IF they agree: commit the explicit .harness/ paths as
        "Milestones: <first id>-<last id>" and carry on to SCOPE.

Run python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-state.py .harness/state.json
    --milestones .harness/milestones.md --requirements .harness/requirements.md
    and STOP on any error.

SCOPE — the milestones to plan, in state.json order:
    every TODO milestone whose plan is not AGREED, starting from the first
    milestone that is not DONE, and stopping
      - before the first BLOCKED milestone (report it: nothing past it can run);
      - after --until <id>, or after --next <n> milestones, if given.
    A milestone already IN_PROGRESS or in REVIEW is skipped: it runs on the
    plan it has.
    IF the scope is empty: STOP — say there is nothing to plan, and why.
    Tell the human which milestones you are about to plan before dispatching.

BRANCH — once, before the first dispatch, if this is a git repository and
the current branch is not already a harness-plans-* branch:
    git checkout -b harness-plans-<YYYYMMDD-HHMM>
    Milestones and plans are committed here, never onto the branch the human
    was on, and the first milestone's branch opens from here when it runs.

FOR each milestone in scope, in order — one at a time, because each plan is
written against the plans before it:
    IF it has no plan:
        invoke a FRESH harness:orchestrator for the PLANNING phase of that
        milestone
        IF SPLIT: the parts replace it in state.json; plan the first part
            next, and its other parts after it, in order. At most 2 splits
            per original milestone; past that, STOP and report.
        IF BLOCKED: stop planning here — later milestones would build on it.
            Report the escalation, and present what is planned so far.
        IF anything other than PLANNED with a plan path, or a response cut off
            before it says so: the phase did not finish. Do not read a
            half-written plan as a draft; stop planning here and report it.
    IF its plan is a DRAFT already: keep it — it is presented with the rest.

PRESENT every DRAFT plan in scope (see below), and ask whether to go ahead.

IF they agree to all, or name the ones they agree:
    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/agree-plan.py .harness/state.json
        <ids> --milestones .harness/milestones.md
        --requirements .harness/requirements.md
    git add .harness && git commit -m "Task plans agreed: <ids>"
    Agree a later plan only if every plan before it in scope is agreed too:
    the loop stops at the first unagreed one, and a later plan rests on the
    earlier ones as written.
    Tell them to /clear and run /harness:implement-loop (or
    /harness:implement), which runs through the agreed milestones and stops
    at the first one without an agreed plan. STOP.

IF they want changes to one or more plans:
    for each, invoke a FRESH harness:orchestrator for the PLANNING phase of
    that milestone, with its plan path and their words verbatim — not your
    paraphrase. IF its return names a later plan that relied on what changed,
    revise that one too, saying what changed. Then PRESENT again.
    This repeats as often as they like; a plan is cheap to change now and
    expensive to change once workers have run it.

IF they edited a plan file themselves:
    the packets and structured state no longer match it. Invoke a FRESH
    harness:orchestrator for the PLANNING phase of that milestone, saying the
    human edited the plan and the rest must be brought in line with it. Then
    PRESENT again.
```

## Presenting the plans

Read each `.harness/plans/M<n>.md` — they are short and written for this. Do
not read the task packets, the source, or the diff: the plans are what is being
agreed, and anything only a packet explains is a gap in a plan to send back.

Start with one short paragraph on the run as a whole: how many milestones, what
the project can do once they are all done, and roughly how much of the work
goes to the expensive model. Then, for each milestone, so someone who has not
been inside the work can decide in a minute or two:

- **What it will do**, in a sentence or two, and how they will be able to see
  it working.
- **The tasks, in order**, one line each in plain words. Say which are cheap
  routine work and which get a stronger, more expensive model, and why — a
  task routed to the top tier names a risk, and that risk is worth a sentence.
- **Anything they should weigh**: the plan's risks and open points, a size
  signal if one was raised, and which of its tasks rest on an earlier
  milestone's planned work.

Then ask one question: go ahead with all of them; go ahead with the first few
(and which); change something (and what); or stop here. Keep task ids, reason
codes and file paths out of the question — they are in the plans for anyone who
wants them.

## Never

- Never set a plan `AGREED` without the human's explicit agreement in this
  conversation. Silence, a question, or "looks fine so far" is not agreement.
- Never write or edit the milestones, a plan, a task packet or structured
  state yourself, apart from `migrate-state.py` and `agree-plan.py`. Every change goes through the orchestrator so the
  three stay consistent.
- Never run `/harness:implement`, or route a task to a worker, from this
  session.
- Never plan two milestones at once. Each plan is written against the ones
  before it, so they are planned in order, each by a fresh orchestrator.
- Never commit milestones or plans onto the branch the human was on.
- Never revise the milestones once any of them has started. Splitting one
  that has not is the planning phase's job; re-cutting one that has is a
  human decision outside this skill.
