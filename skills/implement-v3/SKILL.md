---
name: implement-v3
description: Opt-in, bounded implementation workflow used to evaluate the foreground schema-v2 controller against the stable implement skill before promotion.
context: fork
agent: harness:controller
model: sonnet
effort: medium
---

Implement exactly one current milestone from `.harness/state.json` using the v3
controller contract already in your system prompt.

Start with the fail-closed runtime preflight. Use only schema-v2 guarded state
transitions, fresh foreground subagents, compact artifact returns, independent
task verification, and a fresh milestone reviewer. Stop at the milestone boundary
or a persisted `CONTINUE`, `WAITING_EXTERNAL`, or `BLOCKED` state.

Load detailed procedures only when their phase applies:

- Review: `${CLAUDE_PLUGIN_ROOT}/skills/implement-v3/references/review-loop.md`
- Passing finalization:
  `${CLAUDE_PLUGIN_ROOT}/skills/implement-v3/references/finalization.md`
- External job:
  `${CLAUDE_PLUGIN_ROOT}/agents/references/external-jobs.md`

Do not invoke the stable `implement` skill from this context. Do not perform a
project-level review. Do not continue into a second milestone.
