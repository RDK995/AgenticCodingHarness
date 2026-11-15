# Requirements

## Goal

Add an unattended "implement loop" to the harness plugin: a new skill,
`/harness:implement-loop`, that starts a background driver on the Mac which drives
`/harness:implement` milestone after milestone in fresh headless Claude sessions —
the `/clear`-and-re-invoke cycle the human does by hand today — and sends progress
and stop notifications to the owner's phone through ntfy. The design is ported
from the CodingHarnessv2 loop driver (`~/Projects/CodingHarnessv2/server/scripts/
e2e-driver*.ts`, `e2e-alert.ts`), keeping its start/stop/status shape, sign-in
check, permission boundary and alert transport, but not its end-to-end test-fix
cycle.

## Functional Requirements

- [FR1] A new plugin skill `implement-loop` (invoked as `/harness:implement-loop`)
  starts the loop for the current project. The skill launches the driver and
  returns; it does not itself run milestones.
- [FR2] The driver runs as a detached background process: it survives the
  terminal/Claude window being closed, keeps the Mac awake while it runs
  (`caffeinate`, tied to the driver's own pid), and records its pid and current
  step in a state directory under `.harness/`.
- [FR3] Separate commands, reachable from the skill, **stop** the loop and report
  its **status**. Stop ends the current step cleanly (terminate, then kill after a
  grace period), keeps all committed work and the loop log, and sends the stop
  notification. Status prints running/not running, the pid, the current step and
  the milestone being worked on.
- [FR4] Pre-start checks. Before any step, `start` verifies: (a) `.harness/
  requirements.md` exists with `Open Questions` = `None` (and architecture, if
  present, is AGREED — the same gate `implement` applies); (b) a very short
  headless Claude session, built exactly like every step session, is signed in
  and can see the `harness:implement` skill; (c) the project is not on the main
  branch (`main`/`master`/the repository's default branch); (d) no driver from the
  pid file is still alive. If any check fails the loop does not start: a plain
  message is printed and a phone notification says what to fix.
- [FR5] Each step runs `/harness:implement` in a fresh headless `claude` session
  with the harness plugin loaded, in the project directory. After each session
  ends, the driver reads `.harness/state.json` / `.harness/milestones.md` (not the
  session's own claims alone) to decide what happened, then starts the next fresh
  session. This repeats until a stop condition (FR6) is met.
- [FR6] The loop stops when any of these occurs:
  (a) every milestone is DONE (finished);
  (b) 10 milestones have reached DONE during this start (cap; counted per start);
  (c) the implement session stops for the human — BLOCKED, an escalation, a
  decision needed, a cap (continuation/retry/review cycle) exhausted, a planning
  stop, or any other STOP that is not a normal milestone/phase boundary;
  (d) a step fails to finish twice in a row (crash, no recognisable result, no
  state progress, or its time limit);
  (e) the session reports Claude is signed out or the plan's usage limit is
  reached — stop at once, no second try, with the reset time if given;
  (f) the owner runs stop;
  (g) an unexpected driver error.
  Every stop writes an outcome record to the state directory and sends exactly one
  stop notification.
- [FR7] Phone notifications go through ntfy using the existing private config file
  `~/.config/harness-e2e/alert.json` (`{"ntfy_server": "https://…", "ntfy_topic":
  "<secret>"}`), read at send time. Every message names the project it comes from.
- [FR8] Milestone-start notification: when a milestone begins, a full summary of
  that milestone — its id and name, its goal/purpose, its scope (what it will
  build), and its acceptance criteria — taken from `.harness/milestones.md` /
  `.harness/state.json`. Sent before the session that begins it, or, when the
  milestone was only planned inside that same session, as soon as the driver
  sees it has begun.
- [FR9] Milestone-finish notification: when a milestone reaches DONE, a report
  giving its id, name and result, the number of tasks, how many tasks entered at
  each worker tier (Cheap, Mid, Top) from each task's structured routing tier in
  `state.json`, and the tier(s) of its review(s). Example: "M3 DONE — 7 tasks:
  4 Cheap, 2 Mid, 1 Top; reviewed by Top."
- [FR10] Stop notification: one short plain-words message saying what happened
  (which stop condition from FR6), the milestone/branch it stopped on, and what the
  owner is asked to decide or do, if anything.
- [FR11] Step sessions run unattended with the v2 permission deal: permission
  prompts bypassed so they may edit files, run commands and commit without asking;
  anything that would still prompt is denied; and a deny list (passed as both
  disallowed tools and settings deny rules) blocks pushing, merging, committing on
  main, and rewriting history. The driver itself never pushes or merges.
- [FR12] Sessions use the owner's existing Claude sign-in. The driver passes only
  the minimal environment the sign-in needs (not the whole environment). No
  password, key or token is written to any file, log or commit.
- [FR13] The driver keeps a loop log in its state directory: each step started
  (time, milestone, attempt), its outcome, each notification and whether it was
  sent, and the final outcome. Every child process it starts is logged with its
  pid and command line, never a secret (a prompt is shown by length only).

## Acceptance Criteria

- [AC1] `/harness:implement-loop` exists as a plugin skill, and the plugin loads
  with it (FR1).
- [AC2] With a fake `claude` binary and a notification sink writing to a file,
  `start` launches a detached driver that writes its pid, `status` reports it
  running with its current step, and `stop` ends it, leaving committed work and
  the loop log in place and producing exactly one stop notification (FR2, FR3,
  FR10, FR13).
- [AC3] `start` refuses — no pid file, no step session, a printed reason and one
  notification — when: requirements have open questions; the sign-in check
  session fails; the project is on main; a live driver already exists (FR4).
- [AC4] Driven by a fake implement session that advances a fixture `state.json`,
  the loop runs successive fresh sessions and stops correctly for each FR6
  condition: all DONE, 10-milestone cap, BLOCKED/human stop, two consecutive
  failed steps, signed-out, out-of-usage (no retry, reset time included) (FR5,
  FR6).
- [AC5] For a fixture milestone, the start notification contains its id, name,
  goal, scope and acceptance criteria, and the finish notification contains the
  task count, per-tier task counts matching the fixture's routing tiers, and the
  review tier(s); every message names the project; messages over ntfy's size limit
  are truncated with a visible marker (FR8, FR9, FR7).
- [AC6] The ntfy sender reads `~/.config/harness-e2e/alert.json` at send time,
  POSTs to `<server>/<topic>`, and never lets the topic appear in any output,
  error, log or result; a missing/invalid config or HTTP failure is reported as
  "not sent" without stopping the loop (FR7). Tests never touch the network.
- [AC7] The step session command line carries the bypass/deny-prompts permission
  mode, the plugin directory, and deny rules for push, merge, commit-on-main and
  history rewrite in both forms; its environment contains only the allowed names;
  no secret appears in the command log (FR11, FR12, FR13).
- [AC8] One real start against a small fixture project on the Mac, with the real
  ntfy channel, completes at least one milestone and delivers start, finish and
  stop notifications (HTTP 200 recorded; phone receipt confirmed by the owner).

## Constraints

- Lives in this harness plugin (`AgenticCodingHarness`): a skill under
  `skills/implement-loop/` plus a driver script under `scripts/`.
- Python 3 standard library only, matching the existing `scripts/`; no new
  runtime dependencies (no bun/node).
- Must not change how a single milestone is built: `/harness:implement`, the
  orchestrator, workers, reviewer and the state schema are used as they are.
- macOS (the owner's Mac): `caffeinate` is available; the `claude` CLI is the
  installed one (path overridable).
- ntfy message bodies stay within ntfy's ~4096-byte limit.
- The ntfy topic is a secret: never stored in the repository and never printed.

## Non-Goals

- The CodingHarnessv2 end-to-end test → diagnose → fix → re-run loop.
- Switching CodingHarnessv2's own driver to use this loop.
- Any change to the per-milestone workflow, routing, or `state.json` schema
  (including recording every retry attempt per tier).
- Notification channels other than ntfy; a separate ntfy config or topic.
- Pushing, merging, opening pull requests, or integrating milestone branches.
- Running on Linux/Windows or in the cloud.

## Edge Cases

- `milestones.md` / `state.json` not yet created: the first session plans
  milestones; a planning STOP is an FR6(c) stop.
- A session ends at a normal phase boundary (e.g. implementation done, review
  next) without a milestone reaching DONE: that is progress, not a failure; the
  loop continues with a fresh session.
- A session ends with no change to state and no recognisable result: counts as a
  failed step (FR6(d)).
- A milestone SPLIT into smaller milestones: continue; the cap counts DONE
  milestones only.
- Notification send fails (config missing, network down, HTTP error): the loop
  continues; the failure is recorded in the loop log.
- `stop` while no driver is running: prints "not running", exits cleanly.
- Stale pid file whose process is gone: treated as not running.
- Stop requested mid-session: the session is terminated, uncommitted changes are
  left in the working tree untouched, and the next `implement` run's existing
  interrupted-work handling applies.
- Mac sleeps despite `caffeinate` (lid closed on battery): a step may time out
  and is handled by FR6(d).

## Decisions / Clarifications

- 2026-11-07, owner: the loop's job is "Keep building (Recommended)" — repeat
  `/harness:implement` milestone after milestone; not the v2 test-fix loop, not both.
- Phone channel: "Reuse the same one (Recommended)" — the existing
  `~/.config/harness-e2e/alert.json`, messages labelled with the project.
- Notification moments: "Stops + each milestone (Recommended)", then extended by
  the owner: "Every time a new milestone starts, I would like a full summary of
  what that milestone is. When it completes, I would like a report at the end of
  that milestone of how many tasks and what workers were run, in terms of whether
  it was top, middle, or cheap."
- Worker report detail: "Starting level is fine (Recommended)" — per-task entry
  tier from structured state; not every retry attempt.
- Cost cap: "10 milestones per start".
- Where it runs: "In the background (Recommended)" — detached, survives closing
  the window, keeps the Mac awake, with stop and status commands.
- Permissions: "Same as v2 (Recommended)" — prompts bypassed, push/merge/commit on
  main/history rewrite always denied; refuses to start on main.
- Made by Claude while writing (not asked): Python stdlib implementation; each
  step's time limit and the state-directory location are settled at planning;
  notification send failures never stop the loop.

## Open Questions

None
