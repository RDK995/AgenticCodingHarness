# 05 — Golden path

First validated in **B8**, re-run in **B14**. The baseline: does the workflow work
at all, end to end, with nothing deliberately broken?

## Setup

Agreed requirements only — no `milestones.md`, no `architecture.md`, no source.
The harness plans, implements, reviews and records from a standing start.

Also serves as the no-architecture regression: `architecture.md` is absent, so V1
behaviour applies and nothing should demand one.

```bash
git init -q && git add -A && git commit -qm baseline
```

## Command

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Bash Grep Glob Task Agent" \
  -p "/harness:implement"
```

## Expected outcome

**Mechanically checkable:**

- `.harness/milestones.md` exists, milestone reaches `Status: DONE`.
- Its headings match `skills/implement/references/milestones-template.md` exactly
  and in order.
- `### Architecture` is `N/A` — present, not omitted.
- **Git discipline (B31).** The work is on a milestone branch — `git branch`
  shows one created by the run, and `git rev-parse --abbrev-ref HEAD` is it, not
  the default branch. `### Baseline` records `<sha> on <that branch>` with a sha
  that resolves. Each accepted task is its own commit, so `git log <baseline>..`
  has more than one entry, and `git diff <baseline> HEAD` is the whole
  milestone. **The default branch has no new commits, no remote was contacted,
  and no branch was merged or deleted.** This fixture is the only one that
  exercises the implementation phase from nothing, so it is the only place the
  branch is actually opened.
- **Every commit contains only what belongs in it**, because commits are staged
  by path rather than with `git add -A`. This repository has no `.gitignore`, so
  running the suite leaves an untracked `__pycache__/` — **it must still be
  untracked at the end, and the missing `.gitignore` recorded under
  `### Follow-ups`.** A non-empty `git status` is therefore the *pass* here, and
  a `__pycache__/` committed into the human's history is the failure. (The
  expectation originally read "`git status --porcelain` is empty at the end";
  that was wrong, and the first run under B31 is what showed it.)
- The test suite passes when re-run independently, outside the agent's session.
- `divide(1, 0)` raises rather than returning a sentinel.

**Requires reading the report:**

- Every acceptance criterion carries both implementation and test evidence.
- A fresh review ran and its verdict is recorded.
- A second clean invocation finds every milestone `DONE`, performs only the
  deterministic completion check, reports milestone evidence and stops. It
  dispatches no reviewer, orchestrator, as-built compose agent, or broad test.

## Failure modes worth recognising

- **Skipping `agents/references/planning.md`.** Both the generation invocation and
  the implementation phase must read it; the size/shape check they run is in
  `orchestrator.md` itself, so a phase that skipped the reference can still
  produce a plausible check. Verify from the transcript, not the report.
- Reporting success while `milestones.md` is still `TODO`, or while `Evidence` and
  `Validation` are empty — a claim without the evidence the gate requires.
- Demanding an `architecture.md` that this fixture deliberately does not have.
- Implementing the non-goals (add/subtract/multiply). They are stated as out of
  scope and belong in `### Follow-ups` if raised at all.
- **Working on the default branch, or finishing with the work uncommitted.**
  Either leaves the milestone's diff uncomputable from git, which is the whole
  reason B31 exists. Equally a failure in the other direction: pushing, merging
  the branch back, deleting it, or `git init`-ing anything.
