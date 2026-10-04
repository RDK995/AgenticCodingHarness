# `.harness/plans/M<n>.md` template

One file per milestone, written by the orchestrator's planning phase. A human
reads it to agree the milestone's work before any of it runs, so it is written
in plain words; the exact detail lives in the task packets it links.

```markdown
# M<n> — <Outcome> — task plan

Status: DRAFT

## Summary

<Two or three plain sentences: what this milestone will build, and how anyone
will be able to see it working — the entry point a criterion is exercised
through.>

## Tasks

| Task | What it does | Criteria | Tier | Why this tier | After | Packet |
| --- | --- | --- | --- | --- | --- | --- |
| M<n>-T1 | <one line, plain words> | M<n>-AC1 | Mid | ORDINARY_IMPLEMENTATION | — | `.harness/tasks/M<n>-T1.md` |

## Size check

Criteria: <count>. Signals: <none, or the named signals>. Decision: <run, or
how one signal's seam check came out>.

## Risks and open points

<What the human should weigh before agreeing: an assumption a task rests on, a
place the plan could be wrong, work that will be slow or costly. `None` if
none.>

## Changes during implementation

None
```

## Rules

- `Status` is `DRAFT` until the human agrees it through the `plan`
  skill, which sets `AGREED` with `scripts/agree-plan.py`. Nothing else sets it.
- Every acceptance criterion appears under `Criteria` for at least one task.
- `Tier` and `Why this tier` match the task's `routing` in `.harness/state.json`.
- `After` names the tasks that must be accepted first. A task starts as soon as
  every task in its `After` is accepted, so tasks with nothing outstanding run
  at the same time, in one working tree. Two tasks that can run at the same time
  must not share a path in `Files Allowed To Change`; `agree-plan.py` refuses a
  plan where they do.
- `## Changes during implementation` stays `None` until the plan is agreed. After
  that, the implementation phase records each permitted change here with a
  one-line reason (see "Staying inside the agreed plan" in
  `agents/orchestrator.md`).
