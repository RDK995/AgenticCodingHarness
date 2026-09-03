# harness

A minimal Claude Code plugin that turns rough software requirements into
reviewed, tested implementation through a controlled agentic workflow.

## Install

For local development/testing, point Claude Code at this plugin directory:

```
claude --plugin-dir /path/to/this/repo
```

Inside an already-running session, load it (or pick up changes) with:

```
/reload-plugins
```

No database, MCP server, or other external runtime is required.

## Workflow

1. Run requirement roasting: `/harness:roast-requirements <your rough requirement>`
2. Agree the requirements (answer whatever questions come back; the skill
   won't write `Open Questions: None` until you have)
3. For a **new** project, agree an architecture: `/harness:architect` — it
   proposes components, boundaries and technology choices from the requirements,
   draws them as a diagram, and writes `.harness/architecture.md` once you agree.
   Skip this when adding to
   an existing codebase, where the architecture already exists and the harness
   inspects it instead.
4. Carve an MVP if the full scope is bigger than the first thing worth having:
   `/harness:scope-mvp` — it cuts the agreed scope down to the smallest
   implementation that carries one real user from the entry point to a result
   they actually wanted, asks you whatever the documents can't answer, and
   records what was deferred and the order it comes back in. Skip it when the
   scope is already minimal, or when nothing short of all of it is usable.
5. Run implementation: `/harness:implement`
6. The harness works through milestones on its own — planning them if
   `.harness/milestones.md` doesn't exist yet, then implementing, testing, and
   getting each one fresh-reviewed before moving to the next
7. Review the final result — the harness runs one more fresh, holistic review
   once every milestone is `DONE` and reports `COMPLETE` or asks you to resolve
   a `BLOCKED` state

If you carved an MVP, put it in front of someone before going further — that is
what building the small version first was for. Then re-invoke
`/harness:scope-mvp` to promote the next increment back into scope, reordering
the expansion if what people actually needed wasn't what the plan predicted. If
the first version turned out not to deliver its outcome at all, go back to
`/harness:roast-requirements` with what you learned rather than building a larger
version of it.

When the project has an agreed architecture, each completed milestone also gets
drawn: what it *actually* built, derived from its own diff, into
`.harness/as-built/M<n>.md`. Before the final review those are composed into
`.harness/as-built/drift.md`, which lays the built system against the agreed one
and sorts every component and boundary into *planned and built*, *built but not
planned*, and *planned but never built* — each reconciled against the deviations
you recorded. Divergence with a recorded reason is a decision; divergence
without one is what the comparison exists to surface.

If the harness ever stops with `BLOCKED`, that's deliberate: it hit an
unresolved ambiguity or two failed review cycles, and it needs a decision only
you can make, rather than continuing to guess.

## What it does to your repository

Each milestone runs on its own branch — `m<n>-<slug>`, created when the
milestone opens, off whatever `HEAD` was — and every task the harness accepts is
committed to it. Uncommitted work already in your tree comes across to that
branch and is committed there first, as its own commit, so the branch you were
on is left exactly as you found it. The result is that a milestone's diff is
`git diff <baseline> HEAD` and nothing else: the reviewer, the verifier and the
as-built record all read it straight out of git rather than reconstructing it.

The harness **never pushes, never merges, never deletes a branch, and never
rewrites history it did not create.** Integrating a finished milestone is your
decision, and may be a pull request or a review it cannot see. At `DONE` it
keeps the per-task commits, or squashes them into one when that is plainly your
repository's convention. If the target is not a git repository, it says so once
in the milestone record and runs without any of this rather than running
`git init` behind you.

## State

Everything the harness needs to resume — even in a brand-new Claude session
with no memory of this conversation — lives in two plain Markdown files in the
target project:

```
.harness/requirements.md
.harness/architecture.md   (new projects only)
.harness/milestones.md
.harness/mvp.md            (only if you carved an MVP)
.harness/full/             (only if you carved an MVP — the unedited full scope)
.harness/as-built/         (new projects only — one file per milestone, plus drift.md)
.harness/tasks/            (task packets for a milestone in flight — scratch, not status)
.harness/reviews/          (review reports a fix cycle is answering — scratch, not status)
```

`requirements.md` is the agreed, implementation-ready requirements.
`architecture.md` is the agreed design for a new project — its components,
boundaries and technology choices, plus a log of any deviation made while
building. Milestones say which components they realise, so progress against the
architecture is visible without a second status field to fall out of date.
`as-built/` is the record of what each milestone actually constructed, drawn
from its diff rather than from what it claimed, and the comparison composed from
those records at the end. `milestones.md` tracks each milestone's status,
acceptance criteria, evidence, validation results, and review outcome.
`mvp.md` and `full/` exist only on a project that was carved down to a first
useful version: `requirements.md` and `architecture.md` then hold the MVP, so
everything downstream implements it without needing to know it is one, and the
untouched full scope waits under `full/` to be folded back in an increment at a
time. `mvp.md` also records what counts as delivered, any step a person performs
that the full system would automate, and the order the rest returns in.
`tasks/` holds the task packets for the milestone being built, written once so a
packet is not re-sent to every worker, verifier and retry that needs it; nothing
reads them to learn project status. See `examples/` for what each looks
like once filled in.

## Philosophy

Requirements, tests, diffs and evidence are authoritative.
Agent confidence is not.
