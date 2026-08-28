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
- the diff from `### Baseline` (`git diff <baseline>`), **and
  `git status --porcelain` for uncommitted and untracked work** — the harness does
  not commit after every task, so `git diff <baseline>..HEAD` alone is routinely
  empty even though the milestone was fully implemented. Say in `Evidence` which
  of the two carries this milestone's work, so the review context does not have to
  discover it;
- the requirements the milestone answers to;
- any findings recorded by a previous cycle.

Do not re-run reconnaissance, re-read the architecture in full, or reconstruct
how the implementation was decided. If something you need to judge the work is
missing from the milestone entry, that is a defect in the record — say so, and
record it, rather than working around it in this context.

### What one cycle is, and how it ends

```
Review found something → route each finding as a correction task → validate
                       → record which files the corrections changed
                       → increment Review Cycles
                       → return at REVIEW for the scoped re-review
```

A cycle is one review plus the corrections for it. The review already happened;
you route, validate and record. Findings are **routed like any other task** — a
correction is delegated by tier exactly as the Routing rule in
`${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md` requires, and nothing
about a review finding makes it yours to implement.

**Snapshot the tree before you route anything, and again once the corrections
are validated.** The next review is scoped to what the corrections changed, and
that has to be a real diff: a list of filenames is not one, and since the harness
does not commit after every task, `git diff <baseline> -- <those files>` returns
the milestone's original implementation of them alongside the correction.

Take each snapshot with a throwaway index. It captures **tracked and untracked
work alike**, honours `.gitignore`, and leaves the real index, the worktree and
the stash untouched:

```
IDX=$(mktemp -u)
GIT_INDEX_FILE=$IDX git add -A
TREE=$(GIT_INDEX_FILE=$IDX git write-tree)
rm -f "$IDX"
git commit-tree "$TREE" -p HEAD -m snapshot     # prints the SHA
```

**Do not use `git stash create` here.** It snapshots tracked work only, so a
milestone that added a file without committing it — which this workflow
explicitly permits — loses that file and every correction to it. There is no
`-u` to reach for: `git stash create` takes `[<message>]` and nothing else, so
`-u` is silently swallowed as the message and the command *appears* to work.

Write the correction diff between the two snapshots, and record both:

```
git diff <pre> <post> > .harness/reviews/<milestone>-cycle<n>.patch
```

`Pre-correction: <sha>` and the patch's path go under `### Review`. The patch is
what the next review is given; the ref is what makes it auditable. **Diff the two
snapshots against each other, never a snapshot against the worktree** — an
untracked file exists in the snapshot but not in git's view of the worktree, so a
snapshot-to-worktree diff reports it as *deleted*, which is worse than missing it.
Both snapshot objects are unreachable from any branch, so write the patch in the
same cycle you take them and do not rely on them surviving a `git gc --prune=now`.

**Record the correction diff.** Under `### Review`, list the files the correction
tasks actually changed, for the cycle you just ran. The next review is scoped to
them (see "What a second review sees" in `${CLAUDE_PLUGIN_ROOT}/skills/implement/SKILL.md`),
and that scope is only as trustworthy as this list. If a correction touched a file
no finding named, say so explicitly — that is the fact that widens the next review
back to the whole milestone, and it is invisible unless you record it.

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
