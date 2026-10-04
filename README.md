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
5. Plan: `/harness:plan-milestone`. The first time, it splits the
   requirements into milestones (`.harness/milestones.md`) and checks the
   split with you before going further.
6. It then plans the coming milestones (all remaining by default;
   `--until <id>` or `--next <n>` for fewer). For each, in order, it
   checks the size (splitting it if it is too big), breaks it into tasks, and
   picks which model tier runs each and why — later plans written against the
   earlier ones. Then it walks you through them together. Ask for changes as
   often as you like; it records plans as agreed (`.harness/plans/M<n>.md`)
   only when you say so, on a `harness-plans-*` branch rather than yours.
7. `/clear`, then `/harness:implement-loop` builds the agreed milestones one
   after another — implementing, testing, and getting each fresh-reviewed — and
   stops at the first without an agreed plan (see [Running milestones
   unattended](#running-milestones-unattended)). `/harness:implement` does one
   milestone phase at a time if you'd rather drive it yourself. Repeat from
   step 6 when it runs out of plans.
8. When every milestone is `DONE`, the harness mechanically confirms requirement
   ownership and reports the completed milestones, evidence and follow-ups. It
   does not run an additional project-wide review.

If you carved an MVP, put it in front of someone before going further — that is
what building the small version first was for. Then re-invoke
`/harness:scope-mvp` to promote the next increment back into scope, reordering
the expansion if what people actually needed wasn't what the plan predicted. If
the first version turned out not to deliver its outcome at all, go back to
`/harness:roast-requirements` with what you learned rather than building a larger
version of it.

When the project has an agreed architecture, each completed milestone also gets
drawn: what it *actually* built, derived from its own diff, into
`.harness/as-built/M<n>.md`. Its milestone reviewer grades undeclared divergence
and any existing interfaces touched by that diff. The records are not composed
into a separate project-wide review.

If the harness ever stops with `BLOCKED`, that's deliberate: it hit an
unresolved ambiguity or two failed review cycles, and it needs a decision only
you can make, rather than continuing to guess.

## Running milestones unattended

`/harness:implement` deliberately ends its session at every milestone boundary —
one session carrying several milestones costs several times more — and asks you
to `/clear` and re-invoke. `/harness:implement-loop` automates that:

```
/harness:implement-loop [--until <milestone-id>] [--max <n>] [--permission-mode <mode>]
```

It starts `scripts/implement-loop.py` as its own process, which starts a
brand-new `/harness:implement` session per iteration (a fresh session is the
`/clear`) and decides whether to go again from `.harness/state.json` and
`git rev-parse HEAD` only, never from what the session said. One iteration may
advance only one phase of a milestone; the loop just re-invokes. It stops when:

| Stop | Exit |
| --- | --- |
| every milestone is `DONE`, after one more session in which implement runs its all-DONE check and writes the final report, and that check passes | 0 |
| the next milestone (first not `DONE`, as `/harness:implement` picks it) is `BLOCKED`, or has a status implement has no step for | 3 |
| a session needs a decision from you — the question is printed in the chat; answer there and the loop restarts with your answer | 4 |
| the next milestone is `TODO` and its task plan is not agreed — run `/harness:plan-milestone`, then the loop again | 3 |
| an iteration changed neither `state.json` nor `HEAD` — e.g. it is waiting on a human live check | 3 |
| `--until <id>`: that milestone became the next one (it is not run) | 3 |
| `--max <n>` iterations ran (default 10) | 3 |
| the all-DONE check fails; a session could not start or ended before finishing; state could not be read; or another loop is already running in this checkout | 1 |

**Watching it.** Each session is an ordinary background session
(`claude --bg`), so it looks exactly like one you started yourself:

```
claude attach <id>   # open it in this terminal, live; ← leaves it running
claude agents        # list every session, the loop's included
```

The loop prints the id as each session starts, and one line as each finishes —
milestone, status before → after, `HEAD` before → after. Run from
`/harness:implement-loop`, those lines arrive in the chat that launched it, and
its output is kept in `.harness/evidence/implement-loop/loop-<time>-<pid>.log`
(out of git).
Finished sessions are stopped, not deleted: `claude attach <id>` reopens one.
Unlike other background sessions, the loop's sessions work in your checkout itself, not
a separate worktree — that is where the harness's state and milestone branches
live — so don't edit the same checkout while it runs.
The script also runs directly from a project root:
`python3 /path/to/harness/scripts/implement-loop.py --plugin-dir /path/to/harness`.

**Questions.** A session never waits on you for a decision about the work.
It writes the question down and ends; the loop prints it in the chat that
launched it and stops, so you can read and answer it from your phone. Your
reply, word for word, goes to a fresh session, which records it in the
milestone and acts on it, and the loop carries on. Run directly, the script
exits 4 with the question printed; answer with
`--answer-file <file holding your reply>`.

**Permissions.** A permission prompt waits for you, as in any session: the loop
prints `is waiting for you (permission prompt) -- claude attach <id>`, and
carries on once you have attached and answered. The default
`--permission-mode` is `acceptEdits` — edits inside the project are allowed, and
any shell command your settings don't allow prompts. To be asked less, add an
allowlist to the project's `.claude/settings.json` covering `git` (`add`,
`commit`, `checkout -b`, `rev-parse`, `diff`, `log`, `status`), `python3` for
the harness's scripts, and your project's test, lint and build commands, e.g.:

```json
{
  "permissions": {
    "allow": [
      "Bash(git add:*)", "Bash(git commit:*)", "Bash(git checkout:*)",
      "Bash(git rev-parse:*)", "Bash(git diff:*)", "Bash(git log:*)",
      "Bash(git status:*)", "Bash(python3:*)", "Bash(npm test:*)"
    ]
  }
}
```

`--permission-mode bypassPermissions` turns every check off for the whole
unattended run, including the ones that stop a confused session doing something
destructive. Use it only inside a disposable container or VM with nothing to lose
and no credentials worth taking. The harness's own rules — never push, never
merge, reviewer independence — still hold, because each iteration is an ordinary
`/harness:implement` session.

## What it does to your repository

Each milestone runs on its own branch — `m<n>-<slug>`, created when the
milestone opens, off whatever `HEAD` was — and every task the harness accepts is
committed to it. Uncommitted work already in your tree comes across to that
branch and is committed there first, as its own commit, so the branch you were
on is left exactly as you found it. The result is that a milestone's diff is
`git diff <baseline> HEAD` and nothing else: the reviewer, the verifier and the
as-built record all read it straight out of git rather than reconstructing it.

The harness **never pushes, never merges, never deletes a branch, never squashes,
and never rewrites history.** Integrating a finished milestone is your decision,
and may be a pull request or a review it cannot see. At `DONE` it keeps the
independently verified per-task commits. If the target is not a git repository,
it says so once in the milestone record and runs without any of this rather than
running `git init` behind you.

## State

Everything the harness needs to resume lives in versioned structured state, with
compact Markdown views for people:

```
.harness/requirements.md
.harness/architecture.md   (new projects only)
.harness/milestones.md
.harness/state.json        (authoritative workflow state)
.harness/mvp.md            (only if you carved an MVP)
.harness/full/             (only if you carved an MVP — the unedited full scope)
.harness/as-built/         (new projects only — one file per milestone)
.harness/plans/            (one agreed task plan per milestone)
.harness/tasks/            (task packets for a milestone in flight — scratch, not status)
.harness/reviews/          (review reports a fix cycle is answering — scratch, not status)
.harness/evidence/         (validation artifacts keyed by task/milestone and commit)
```

`requirements.md` is the agreed, implementation-ready requirements.
`architecture.md` is the agreed design for a new project — its components,
boundaries and technology choices, plus a log of any deviation made while
building. Milestones say which components they realise, so progress against the
architecture is visible without a second status field to fall out of date.
`as-built/` records what each milestone actually constructed, drawn from its
diff rather than from what it claimed. `state.json` carries statuses, stable ids,
requirement ownership, review cycles and artifact paths. `milestones.md` is the
compact human-readable view and is checked against that authority on every
transition.
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

## Measuring a run

Use `python3 .harness-dev/measure-context.py <session-dir> [more...] --json report.json`
to produce deduplicated token traffic, estimated cost, role/milestone splits,
peak contexts, polling, repeated commands, duplicate validation, review/diff
counts, and the harness version and commit. Price assumptions are replaceable
with `--prices <json>`.

After the behavioural fixtures and independent gates are confirmed, copy
`examples/accuracy-evidence.example.json` and run
`python3 .harness-dev/check-efficiency.py report.json --accuracy-evidence <file>`.
This fails if any release threshold in the token-efficiency plan is missed.
