# Milestones

## M1 — The loop starts in the background, reports its status, and stops cleanly

Status: DONE

### Outcome

Walking skeleton of the unattended loop. `/harness:implement-loop` exists as a
plugin skill (`skills/implement-loop/SKILL.md`) whose start, status and stop
commands call one stdlib Python driver, `scripts/implement-loop.py`. `start`
launches a detached driver (its own session, surviving the terminal closing) that
holds `caffeinate -w <driver pid>`, records its pid and current step, runs steps
through a configurable `claude` binary (a fake in tests), and keeps a loop log.
`stop` ends the step and the driver cleanly and sends exactly one stop
notification through a pluggable sink (a file sink in tests; ntfy arrives in M5).

Settled at planning: the state directory is `.harness/loop/` in the target
project (`driver.pid`, `current-step.json`, `loop.log`, `commands.log`,
`outcome.json`). The driver writes `.harness/loop/.gitignore` containing `*` so
that the orchestrator's `git add .harness` never commits loop state. Kill grace
period: 20 seconds, overridable per start.

Complexity signals: CONCURRENCY_LIFECYCLE (one signal; seam check done — the
lifecycle change is the slice's whole outcome and carries no live-environment
proof, so it is not split further).

Tests follow the repository convention: stdlib `unittest` scripts under
`.harness-dev/`, run as `python3 .harness-dev/test-<name>.py`.

### Architecture

N/A

### As-Built

N/A

### Acceptance Criteria
- [x] M1-AC1 `/harness:implement-loop` exists as a plugin skill under `skills/implement-loop/`, and `claude --plugin-dir <this repository>` lists it with no plugin load errors (AC1, FR1).
- [x] M1-AC2 With a fake `claude` binary and a file notification sink, `scripts/implement-loop.py start` returns promptly while a detached driver (in its own session, not a child of the invoking shell, with `caffeinate -w <driver pid>` running) writes its pid and current step under `.harness/loop/`; `status` prints running, the pid, the current step and the milestone being worked on (AC2, FR2, FR3).
- [x] M1-AC3 `stop` terminates the running step (SIGTERM, then SIGKILL after the grace period) and the driver, clears the pid file, leaves committed work and `.harness/loop/loop.log` in place, and produces exactly one stop notification in the sink (AC2, FR3).
- [x] M1-AC4 `stop` and `status` with no driver, or with a stale pid file whose process is gone, print "not running" and exit 0 (Edge Cases).
- [x] M1-AC5 `.harness/loop/loop.log` records each step started (time, milestone, attempt), its outcome, each notification and whether it was sent, and the final outcome; every child process is logged with its pid and command line, a prompt shown by length only; nothing under `.harness/loop/` is staged by `git add .harness` (FR13).

### Baseline
5eccdccf677779cbe92a845bcd4ca76da6dd70b4 on m1-loop-background-start-stop

### Evidence
Tasks (entry tier, rungs):
- M1-T1 skill file — Cheap, attempt 1, PASS (`.harness/evidence/M1-T1-verifier.log`), commit dd277a5
- M1-T2 detached driver start/status/stop — Top, attempt 4, PASS — routed Top: DIFFICULT_CONCURRENCY (`.harness/evidence/M1-T2-verifier.log`, `-run2.log`), commit b1b3188
- M1-T3 loop/commands log content, loop state unstaged — Cheap, attempt 1, PASS (`.harness/evidence/M1-T3-verifier.log`), commit 5f8c1ef

Per criterion:
- M1-AC1: `.harness/evidence/M1-AC1-plugin-listing.log` — `claude --plugin-dir <repo> -p ...` EXIT_STATUS=0, `SKILL:harness:implement-loop`, `PLUGIN_ERRORS: none`; skill test 3/3 OK.
- M1-AC2: `test_start_detaches_driver_and_status_reports_it`.
- M1-AC3: `test_stop_ends_step_and_driver_leaving_log_and_git_untouched`, `test_stop_kills_step_that_ignores_sigterm_after_grace`.
- M1-AC4: `test_status_and_stop_report_not_running_without_live_driver`.
- M1-AC5: `test_loop_log_records_step_lifecycle_with_timestamps`, `test_loop_log_records_unsent_notification_without_notify_file`, `test_commands_log_records_children_with_prompt_by_length`, `test_git_add_stages_fixture_changes_but_never_loop_state`.

### Validation
For the reviewer to run once:
- `python3 .harness-dev/test-implement-loop.py` (10 tests; verifier run exit 0)
- `python3 .harness-dev/test-implement-loop-skill.py` (3 tests; verifier run exit 0)

Permitted pre-existing failure (F1): `python3 .harness-dev/test-orchestrator-inventory.py` fails `test_core_stays_compact` — `agents/orchestrator.md` is 730 lines against a 720-line cap. It was already 730 lines at baseline 5eccdcc; the M1 diff does not touch `agents/`. Not an M1 regression; tracked under Follow-ups.

### Review
- Cycle 1 — tier Top (opus), reason DIFFICULT_CONCURRENCY, diff 5eccdcc..53b8390. Verdict CHANGES REQUIRED, scope RECORD_ONLY; per-criterion M1-AC1..AC5 all PASS. Report `.harness/reviews/M1-cycle1.md`. Findings: F1 IMPORTANT, F2 OPTIONAL.
- Review attempts: 4. Attempts 1–3 were interrupted (attempt 3 reached its verdict, but the report save failed). The human authorised attempt 4, beyond the 2-retry cap.
- Record-only correction: pre-correction 53b8390; F1 and F2 resolved by `.harness/` edits; `check-state.py --record-only 53b8390 HEAD` and the consistency check both OK.

### Review Cycles
0

### Follow-ups
- Interface defaults untested: `HARNESS_LOOP_CLAUDE` fallback and `--grace` default 20 s; the `stop` timeout branch (exit 1 after grace+10 s) is untested and neither force-kills nor notifies.
- `step N outcome:` is logged whenever a step ran, including a step stopped mid-run (`scripts/implement-loop.py` L320-322); it is absent only when `stop` arrives before the step starts.
- `run()` hardcodes step 1 / attempt 1; M2 adds the step counter.
- Pre-existing, outside M1: `agents/orchestrator.md` exceeds the 720-line cap in `test-orchestrator-inventory.py::test_core_stays_compact` (730 lines since baseline 5eccdcc); fix separately.

## M2 — Each step is a fresh, locked-down `/harness:implement` session, and the loop advances on recorded state

Status: REVIEW

### Outcome

The driver's step becomes the real one: a fresh headless `claude` session per
step, with the harness plugin loaded, running `/harness:implement` in the project
directory under the v2 permission deal (prompts bypassed, anything still
prompting denied, push/merge/commit-on-main/history-rewrite denied in both
forms), with a minimal environment. After each session the driver judges the
step from `.harness/state.json` / `.harness/milestones.md`, continues on
progress, and stops when every milestone is DONE. One command-line builder
produces the step session; M3's sign-in check reuses it unchanged.

Settled at planning: the per-step time limit is 3 hours (the v2 build-step
limit), overridable per start; a step past it is terminated, then killed after
the grace period, and counts as a failed step.

### Architecture

N/A

### As-Built

N/A

### Acceptance Criteria
- [ ] M2-AC1 Driven through `start` by a fake implement session that advances a fixture `.harness/state.json`, the driver runs successive fresh `claude` processes, one per step, in the project directory, each invoking `/harness:implement`, and decides each step's result from `state.json` / `milestones.md` rather than from the session's output alone (FR5).
- [ ] M2-AC2 A session ending at a normal phase boundary (for example a milestone left at REVIEW) with state progress counts as progress and the next fresh session starts; when every milestone is DONE the loop stops as finished (FR5, FR6(a), Edge Cases).
- [ ] M2-AC3 The step command line carries `--permission-mode bypassPermissions`, the setting that denies anything that would still prompt, `--plugin-dir <harness root>`, and deny rules for push, merge, commit on main and history rewrite both as `--disallowedTools` values and inside `--settings` `permissions.deny`; the driver itself runs no push or merge (AC7, FR11).
- [ ] M2-AC4 The step environment contains only the allowed names (PATH, HOME, USER, GIT_TERMINAL_PROMPT, and the named sign-in variables when set); a fake secret seeded in the parent environment appears in neither the child environment, `commands.log` nor `loop.log` (AC7, FR12, FR13).
- [ ] M2-AC5 A step that exceeds the step time limit (3 hours by default, overridable per start) is terminated, killed after the grace period if still alive, and recorded in the loop log as a failed step (FR5, Edge Cases).

### Baseline
8c676453196d66e83d2810645cf1490176967854 on m2-fresh-locked-down-steps

### Evidence
- M2-T1 (Top, attempt 4, PASS; routed Top: SECURITY): step-session builder `session_command` - .harness/evidence/M2-T1-verifier.log (python3 .harness-dev/test-implement-loop.py exit 0, 15 tests OK)
- M2-T2 (Mid, attempt 3, PASS; routed Mid: ORDINARY_IMPLEMENTATION): loop advances on recorded state via pure `judge_step` - .harness/evidence/M2-T2-verifier.log (python3 .harness-dev/test-implement-loop.py exit 0, 20 tests OK)
- M2-T3 (Mid, attempt 3, PASS; routed Mid: ORDINARY_IMPLEMENTATION): step time limit, --step-timeout - .harness/evidence/M2-T3-verifier.log (python3 .harness-dev/test-implement-loop.py exit 0, 24 tests OK)
- M2-C1-F1 (Top, attempt 4, PASS; routed Top: SECURITY): deny-list gaps (cycle-1 F1), commit a677a80 - .harness/evidence/M2-C1-F1-verifier.log (python3 .harness-dev/test-implement-loop.py exit 0, 25 tests OK)
- M2-C1-F3 (Cheap, attempt 1, PASS): --step-timeout must be finite and positive (cycle-1 F3), commit 607442d - .harness/evidence/M2-C1-F3-verifier.log (python3 .harness-dev/test-implement-loop.py exit 0, 26 tests OK)
- M2-AC1: .harness/evidence/M2-T2-verifier.log: test_loop_runs_successive_fresh_steps_until_every_milestone_is_done (4 runs, 4 distinct pids, cwd == project, -p /harness:implement each); test_state_not_output_decides_the_step_result
- M2-AC2: .harness/evidence/M2-T2-verifier.log: same 4-run test (M1 REVIEW -> 'step 1 outcome: progress' -> step 2 started; ends 'finished: every milestone is DONE', one notification); test_nonzero_exit_with_state_advanced_to_all_done_is_finished; test_milestones_file_only_change_counts_as_progress
- M2-AC3: .harness/evidence/M2-T1-verifier.log: test_builder_returns_locked_down_command, test_step_runs_locked_down_with_minimal_environment (bypassPermissions, --permission-prompts none, --plugin-dir, DENY_RULES in --disallowedTools and --settings permissions.deny); test_driver_source_runs_no_push_or_merge
- M2-AC4: .harness/evidence/M2-T1-verifier.log: test_step_runs_locked_down_with_minimal_environment (env names subset of allowed, GIT_TERMINAL_PROMPT=0); test_parent_secret_reaches_neither_step_nor_logs
- M2-AC5: .harness/evidence/M2-T3-verifier.log: test_step_over_time_limit_is_terminated_and_recorded_as_failed, test_step_over_time_limit_ignoring_sigterm_is_killed_after_grace, test_timed_out_step_is_failed_even_if_state_advanced, test_step_timeout_defaults_to_three_hours_and_is_listed_in_help

### Validation
- python3 .harness-dev/test-implement-loop.py — PASS, 26 tests after cycle-1 corrections (.harness/evidence/M2-C1-F3-verifier.log); earlier 24 tests (.harness/evidence/M2-T3-verifier.log); milestone validation command for the reviewer. Diff: git diff 8c676453196d66e83d2810645cf1490176967854 HEAD

Permitted pre-existing failure (cycle-1 F2): `python3 .harness-dev/test-orchestrator-inventory.py` fails `test_core_stays_compact` — `agents/orchestrator.md` is 730 lines against a 720-line cap. It was already 730 lines at baseline 8c67645 (last changed in 94cfccd); the M2 diff does not touch `agents/`. Not an M2 regression; tracked under Follow-ups (.harness/evidence/M2-review.log).

### Review
- Cycle 1 — tier Top (opus), reason SECURITY (reviewer tier not stated in the report; recorded after M2-T1's SECURITY routing), diff 8c676453196d66e83d2810645cf1490176967854..02a06cbf2c810b316a6cfd4c69c0c61b5315a6c5. Verdict CHANGES REQUIRED, scope SUBSTANTIVE; per-criterion M2-AC1..AC5 all PASS. Report `.harness/reviews/M2-cycle1.md`. Findings: F1 IMPORTANT, F2 IMPORTANT, F3 OPTIONAL.
- Pre-correction: 02a06cbf2c810b316a6cfd4c69c0c61b5315a6c5
- F2: resolved record-only (permitted pre-existing failure, see Validation and Follow-ups).
- F1: resolved by M2-C1-F1 (a677a80). F3: resolved by M2-C1-F3 (607442d).
- Cycle 1 corrections: commits 19721a9 (record), a677a80, 607442d. Correction diff: `git diff 02a06cbf2c810b316a6cfd4c69c0c61b5315a6c5 HEAD`. Files changed outside `.harness/`: scripts/implement-loop.py, .harness-dev/test-implement-loop.py — both named by cycle-1 findings (F1, F3); no file changed that no finding named.

### Review Cycles
1

### Follow-ups
- Size check at pickup: 5 criteria; shape OK (start entry point); one signal CONCURRENCY_LIFECYCLE (step time limit) - seam check: reuses M1 terminate_step, same outward outcome, kept whole.
- M2-T1: deny rules (Bash(<cmd>:*) prefix rules) are checked only against a fake claude; whether the real CLI matches them, and variants such as `git -C . push`, an alias, or a script, is unproven. Live check belongs with M3-AC5/M7.
- M2-T1: verifier flagged an unauthorised assertion loosening in test_start_detaches_driver_and_status_reports_it (exact argv -> -p followed by /harness:implement); forced by M2-AC3, packet amended to authorise it, accepted.
- M2-T2: interim rule - one failed step (no state progress) stops the loop; M4-AC3 replaces it with two consecutive failed steps.
- Pre-existing, outside M2: agents/orchestrator.md exceeds the 720-line cap in test-orchestrator-inventory.py::test_core_stays_compact (730 lines, unchanged since 94cfccd); accepted for M2's gate (cycle-1 F2), fix separately.
- Cycle-1 F1: the new deny rules are checked as strings only; the matching behaviour (`:*` needs a following space; mid-pattern `*` becomes `.*`) was read from the installed CLI 2.1.319 binary by the worker, not observed live. The live M3-AC5/M7 check should try `git branch -m main`, `git commit -a --amend` and `git reset HEAD~1`.
- Cycle-1 F1: still not denied (outside F1's list): `git reset <sha>`, `git reset origin/main`, `git reset HEAD@{n}`; the amend rule also denies a commit whose message contains ` --amend` (safe side).
- Cycle-1 F3: `--step-timeout -inf` in the space form is rejected by argparse (multi-line usage, exit 2, no driver) before the new check; the test covers only the `--step-timeout=VALUE` form and asserts the `--step-timeout` substring, not the full message wording.

## M3 — `start` refuses to begin when the project is not safe to run

Status: TODO

### Outcome

The pre-start gate. Before any step, `start` checks the requirements gate (and
an AGREED architecture when one exists), runs a very short sign-in check session
built by M2's step-session builder, refuses on the main/master/default branch,
and refuses when a live driver already exists. A refusal creates no pid file and
no step session, prints a plain reason and sends one notification. The sign-in
check is also proved once against the real installed `claude` on the owner's Mac,
so the shared session command line meets the real CLI early rather than at M7.

Settled at planning: the sign-in check session's time limit is 2 minutes.

Complexity signals: IMPLEMENTATION_PLUS_LIVE_PROOF (one signal; seam check done —
the live proof is a single read-only check-session run with no lifecycle or
concurrency change, kept here because it retires the highest integration risk
first).

### Architecture

N/A

### As-Built

N/A

### Acceptance Criteria
- [ ] M3-AC1 With `.harness/requirements.md` missing or with `Open Questions` other than `None` (or an `architecture.md` that is not AGREED), `start` refuses: no pid file, no step session, a printed plain reason, and exactly one notification saying what to fix (AC3, FR4(a)).
- [ ] M3-AC2 When the sign-in check session fails (a fake `claude` reporting signed out, or not seeing `harness:implement`), `start` refuses the same way; the check session is built by the same builder as step sessions (same permission flags, plugin dir and environment) with a 2-minute limit (AC3, FR4(b)).
- [ ] M3-AC3 On `main`, `master` or the repository's default branch, `start` refuses the same way (AC3, FR4(c)).
- [ ] M3-AC4 When the pid file names a live driver, `start` refuses the same way and leaves the existing driver running and its state untouched (AC3, FR4(d)).
- [ ] M3-AC5 The sign-in check, run through the driver's entry point against the real installed `claude` on the owner's Mac, passes and confirms `harness:implement` is visible; the exact command (prompt by length) and its result are recorded (FR4(b)).

### Baseline

### Evidence

### Validation

### Review

### Review Cycles
0

### Follow-ups

## M4 — The loop stops for the right reason and tells the owner in one plain message

Status: TODO

### Outcome

Every FR6 stop condition is detected and handled: the 10-milestone cap per
start, a human stop from the implement session, two consecutive failed steps,
signed-out or out-of-usage, the owner's stop and an unexpected driver error.
Every stop writes `.harness/loop/outcome.json` and sends exactly one short
plain-words stop notification.

### Architecture

N/A

### As-Built

N/A

### Acceptance Criteria
- [ ] M4-AC1 Driven through `start` by a fake session that completes a milestone per step, the loop stops after 10 milestones reach DONE during this start; milestones that were already DONE before the start, and milestones split into parts that are not yet DONE, do not count (AC4, FR6(b), Edge Cases).
- [ ] M4-AC2 A session that stops for the human — a milestone BLOCKED, an escalation, a decision needed, an exhausted continuation/retry/review-cycle cap, a planning stop (including the first session when `milestones.md` does not yet exist), or any other STOP that is not a normal phase boundary — stops the loop without another session (AC4, FR6(c), Edge Cases).
- [ ] M4-AC3 Two consecutive failed steps (crash, no recognisable result, no state progress, or the time limit) stop the loop; a single failed step followed by a step that makes progress does not (AC4, FR6(d)).
- [ ] M4-AC4 Session output reporting that Claude is signed out or that the plan's usage limit is reached stops the loop at once with no second session, and the stop message includes the reset time when the output gives one (AC4, FR6(e)).
- [ ] M4-AC5 Every stop — including the owner's `stop` and an unexpected driver error — writes `.harness/loop/outcome.json` and sends exactly one stop notification naming which condition occurred, the milestone and branch it stopped on, and what the owner is asked to decide or do, if anything (FR6, FR6(f), FR6(g), FR10).

### Baseline

### Evidence

### Validation

### Review

### Review Cycles
0

### Follow-ups

## M5 — Notifications reach the owner's phone through ntfy without ever revealing the topic

Status: TODO

### Outcome

The ntfy sender becomes the default sink behind the same notification seam the
file sink uses, without changing any notification's content. It reads
`~/.config/harness-e2e/alert.json` at send time, POSTs to `<server>/<topic>`,
treats the topic as a secret everywhere, labels every message with the project,
truncates bodies to ntfy's size limit, and never lets a failed send stop the
loop. Tests use a stub endpoint on 127.0.0.1 or an injected opener; they never
touch the external network.

### Architecture

N/A

### As-Built

N/A

### Acceptance Criteria
- [ ] M5-AC1 A loop run through `start` and `stop` with the alert config path pointed at a test config sends its stop notification through the ntfy sender, which reads the config at send time and POSTs the body to `<ntfy_server>/<ntfy_topic>` on a local stub; no test touches the external network (AC6, FR7).
- [ ] M5-AC2 The topic never appears in stdout, stderr, `loop.log`, `commands.log`, `outcome.json`, or any error or exception text, including when the POST fails (AC6, FR7).
- [ ] M5-AC3 A missing or invalid config, a network failure, or an HTTP error status is recorded in `loop.log` as "not sent" with a reason, and the loop keeps running (AC6, Edge Cases).
- [ ] M5-AC4 Every message names the project it comes from, and a body over ntfy's 4096-byte limit is truncated to fit with a visible truncation marker (AC5, FR7).

### Baseline

### Evidence

### Validation

### Review

### Review Cycles
0

### Follow-ups

## M6 — Each milestone's start and finish reach the owner as a full summary and a worker-tier report

Status: TODO

### Outcome

The driver announces milestones. When a milestone begins, it sends a full
summary taken from `.harness/milestones.md` / `.harness/state.json`; when one
reaches DONE, it sends a report of its task count, the entry tier of each task
from structured routing, and its review tier(s). No change to the state schema:
only fields already recorded are read.

### Architecture

N/A

### As-Built

N/A

### Acceptance Criteria
- [ ] M6-AC1 For a fixture milestone, the start notification contains its id, name, goal/purpose, scope and acceptance criteria, taken from `milestones.md` / `state.json`, and is sent before the session that begins it (AC5, FR8).
- [ ] M6-AC2 When the milestone was only planned inside a session (no `milestones.md` before it), its start notification is sent as soon as the driver sees after that session that it has begun (FR8, Edge Cases).
- [ ] M6-AC3 When a milestone reaches DONE, the finish notification gives its id, name and result, the task count, the per-tier counts of task entry tiers (Cheap, Mid, Top) matching the fixture's `routing.tier` values, and the tier(s) of its review(s), in the shape "M3 DONE — 7 tasks: 4 Cheap, 2 Mid, 1 Top; reviewed by Top." (AC5, FR9).
- [ ] M6-AC4 A loop run through `start` with a fake session advancing a fixture over two milestones leaves, in the sink, each milestone's start and finish notification exactly once and in order, each naming the project (AC5, FR8, FR9).

### Baseline

### Evidence

### Validation

### Review

### Review Cycles
0

### Follow-ups

## M7 — One real unattended run builds a milestone, and the owner's phone hears about it

Status: TODO

### Outcome

Live proof of the whole loop on the owner's Mac: a real `start` against a small
fixture project outside this repository, with the real `claude` sign-in and the
real ntfy channel, completes at least one milestone and delivers start, finish
and stop notifications. This milestone adds no new behaviour; a defect found
here is routed as a correction against the requirement it breaks.

Complexity signals: IMPLEMENTATION_PLUS_LIVE_PROOF (separated from all
implementation milestones so the live run proves finished behaviour).

### Architecture

N/A

### As-Built

N/A

### Acceptance Criteria
- [ ] M7-AC1 One real `start` against a small fixture project on the owner's Mac (on a non-main branch, with agreed requirements) runs unattended and completes at least one milestone to DONE, shown by the fixture's `state.json` and its milestone branch commits (AC8).
- [ ] M7-AC2 The milestone start, milestone finish and stop notifications are each sent through the real ntfy channel, with HTTP 200 recorded for each in `loop.log` (AC8).
- [ ] M7-AC3 The owner confirms the three notifications arrived on the phone, and that confirmation is recorded with its date (AC8).
- [ ] M7-AC4 After the run, the ntfy topic and any credential appear in none of `loop.log`, `commands.log`, `outcome.json`, the fixture repository or this repository, checked by a recorded search (AC6, FR12).

### Baseline

### Evidence

### Validation

### Review

### Review Cycles
0

### Follow-ups
