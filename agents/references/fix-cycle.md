# One fix cycle

Read this when you were dispatched with a review report path. An implementation
phase never needs it — it returns at `REVIEW` and the review that follows is
invoked by the skill, not by you.

## One fix cycle

**This is a whole invocation, not the tail of the implementation one.** You are
here because a fresh review returned findings against a milestone at `REVIEW`.

**The `implement` skill invokes the reviewer, not you.** A review that passes has
nothing to route, and instantiating a coordinator to discover that is the most
expensive way to learn it. You are invoked for the half that has work in it.

Your context holds the milestone entry, the review report at the path you were
given, and what you read to route the corrections — not the planning, the packets
or the task results that produced the work, which are in `.harness/milestones.md`
where they belong.

Reconstruct what you need and no more:

- the milestone entry — criteria, `Evidence`, `Validation`, `Review Cycles`, and
  the tier recorded against each task;
- the review report at `.harness/reviews/<milestone>-cycle<n>.md`, whose path you
  were given. Read it once. Do not copy its findings back out in full — a
  correction packet names the finding and points at the path, exactly as a task
  packet does;
- the diff from `### Baseline` — `git diff <baseline> HEAD`, on the milestone
  branch that field names. Every accepted task was committed, so that diff is the
  milestone. If `git status --porcelain` shows anything outside `.harness/`,
  something was left uncommitted: say so in `Evidence` rather than letting the
  next review discover a diff that does not match the tree;
- the requirements the milestone answers to;
- any findings recorded by a previous cycle.

Do not re-run reconnaissance, re-read the architecture in full, or reconstruct
how the implementation was decided. If something you need to judge the work is
missing from the milestone entry, that is a defect in the record — say so, and
record it, rather than working around it in this context.

### What one cycle is, and how it ends

```
Review found something → record Pre-correction: git rev-parse HEAD
                       → route each finding as a correction task
                       → commit each accepted correction
                       → validate
                       → record which files the corrections changed
                       → increment Review Cycles
                       → return at REVIEW for the scoped re-review
```

A cycle is one review plus the corrections for it. The review already happened;
you route, validate and record. Findings are **routed like any other task** — a
correction is delegated by tier exactly as the Routing rule in
`${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md` requires, and nothing
about a review finding makes it yours to implement.

**Record `Pre-correction: <sha>` before you route anything** — `git rev-parse
HEAD`, on the milestone branch, while the tree still holds only what the review
judged. Then commit each accepted correction exactly as the implementation phase
commits each accepted task (see "Git discipline in the target repository" in
`${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md`), so that when the cycle ends the
correction diff is simply:

```
git diff <Pre-correction> HEAD
```

That range is what the next review is scoped to, and the ref under `### Review`
is what makes the scope auditable. **Take the ref before routing, not after.**
Taken afterwards it includes the corrections it was supposed to bound, and the
scoped review then reads an empty diff and passes everything.

This is why the branch-and-commit rule exists. Without it there is no ref to
take: a milestone's implementation and its corrections sit in one dirty tree,
`git diff <baseline> -- <those files>` returns the implementation alongside the
correction, and a file the milestone added but never committed is invisible to
any diff taken against the worktree. The harness used to snapshot the tree twice
through a throwaway index and write a patch file to work around all of that.
**That mechanism is gone.** If you find a `.patch` path recorded by an older
cycle, treat it as the correction diff for that cycle and carry on; do not
recreate one.

**Record which files the corrections changed.** Under `### Review`, for the cycle
you just ran — `git diff --name-only <Pre-correction> HEAD`. The next review is
scoped by it (see "What a second review sees" in
`${CLAUDE_PLUGIN_ROOT}/skills/implement/SKILL.md`), and that scope is only as
trustworthy as this list. If a correction touched a file no finding named, say so
explicitly — that is the fact that widens the next review back to the whole
milestone, and it is invisible unless you record it.

End the invocation in one of three states, and say which in your return:

- **`REVIEW`** — findings were fixed and validated; the work needs a fresh review
  it must not get from this context.
- **`CONTINUE`** — you reached the turn budget with corrections still outstanding.
  Record which findings you corrected and which remain, and **do not increment
  `### Review Cycles`**: the cycle is unfinished, so it has not happened. The
  skill invokes a fresh fix cycle with the same report path. Returning `REVIEW`
  here instead would send half-corrected work to a reviewer and spend a cycle of
  the cap on it.
- **`BLOCKED`** — see the cap below, or the Human Escalation Contract in
  `${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md`.

**You cannot return `DONE`.** Only a passing review can complete a milestone, and
the skill records that directly from the reviewer's verdict. There is no path to
`DONE` through this invocation.

Allow at most **2 review/fix cycles per milestone**, counted in
`### Review Cycles` and carried across invocations by that field — it is the only
memory of the count, so increment it before you return or the cap silently
resets. If BLOCKER or IMPORTANT findings remain after 2 cycles, set the milestone
to `BLOCKED` and escalate — the Human Escalation Contract is in
`${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md` — instead of trying a third time. This same
2-cycle cap and escalation applies when you're handling a correction after a
failed **final** review (Final Reviewer → you → bounded correction task →
implement → validate → fresh final review).
