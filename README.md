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
3. Run implementation: `/harness:implement`
4. The harness works through milestones on its own — planning them if
   `.harness/milestones.md` doesn't exist yet, then implementing, testing, and
   getting each one fresh-reviewed before moving to the next
5. Review the final result — the harness runs one more fresh, holistic review
   once every milestone is `DONE` and reports `COMPLETE` or asks you to resolve
   a `BLOCKED` state

If the harness ever stops with `BLOCKED`, that's deliberate: it hit an
unresolved ambiguity or two failed review cycles, and it needs a decision only
you can make, rather than continuing to guess.

## State

Everything the harness needs to resume — even in a brand-new Claude session
with no memory of this conversation — lives in two plain Markdown files in the
target project:

```
.harness/requirements.md
.harness/milestones.md
```

`requirements.md` is the agreed, implementation-ready requirements.
`milestones.md` tracks each milestone's status, acceptance criteria, evidence,
validation results, and review outcome. See `examples/` for what both look
like once filled in.

## Philosophy

Requirements, tests, diffs and evidence are authoritative.
Agent confidence is not.
