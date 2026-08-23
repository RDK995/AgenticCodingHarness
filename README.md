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
4. Run implementation: `/harness:implement`
5. The harness works through milestones on its own — planning them if
   `.harness/milestones.md` doesn't exist yet, then implementing, testing, and
   getting each one fresh-reviewed before moving to the next
6. Review the final result — the harness runs one more fresh, holistic review
   once every milestone is `DONE` and reports `COMPLETE` or asks you to resolve
   a `BLOCKED` state

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

## State

Everything the harness needs to resume — even in a brand-new Claude session
with no memory of this conversation — lives in two plain Markdown files in the
target project:

```
.harness/requirements.md
.harness/architecture.md   (new projects only)
.harness/milestones.md
.harness/as-built/         (new projects only — one file per milestone, plus drift.md)
```

`requirements.md` is the agreed, implementation-ready requirements.
`architecture.md` is the agreed design for a new project — its components,
boundaries and technology choices, plus a log of any deviation made while
building. Milestones say which components they realise, so progress against the
architecture is visible without a second status field to fall out of date.
`as-built/` is the record of what each milestone actually constructed, drawn
from its diff rather than from what it claimed, and the comparison composed from
those records at the end. `milestones.md` tracks each milestone's status,
acceptance criteria, evidence, validation results, and review outcome. See `examples/` for what each looks
like once filled in.

## Philosophy

Requirements, tests, diffs and evidence are authoritative.
Agent confidence is not.
