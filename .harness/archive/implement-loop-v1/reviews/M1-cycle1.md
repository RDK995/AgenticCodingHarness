# M1 review — cycle 1

Diff: `git diff 5eccdccf677779cbe92a845bcd4ca76da6dd70b4 HEAD` (HEAD 53b8390, branch m1-loop-background-start-stop)
Validation evidence: `.harness/evidence/M1-review.log` ("Review retry 3" whole suite; "Review retry 4" focused re-run)

Verdict: CHANGES REQUIRED (Scope: RECORD_ONLY)

## Acceptance criteria

Acceptance Criterion:
M1-AC1 `/harness:implement-loop` exists as a plugin skill under `skills/implement-loop/`, and `claude --plugin-dir <this repository>` lists it with no plugin load errors.

Implementation Evidence:
`skills/implement-loop/SKILL.md` (frontmatter name/description; runs exactly one of start/status/stop via `${CLAUDE_PLUGIN_ROOT}/scripts/implement-loop.py`).

Test Evidence:
`.harness-dev/test-implement-loop-skill.py` 3/3 OK (re-run); `.harness/evidence/M1-AC1-plugin-listing.log` (`SKILL:harness:implement-loop`, `PLUGIN_ERRORS: none`); `claude plugin validate .` passed (README advice warning only, pre-existing).

Result:
PASS

Acceptance Criterion:
M1-AC2 `start` returns promptly while a detached driver (own session, `caffeinate -w <driver pid>`) writes its pid and current step under `.harness/loop/`; `status` prints running, pid, current step and milestone.

Implementation Evidence:
`scripts/implement-loop.py` `command_start` L340-375 (`start_new_session=True`, waits ≤4 s for pid file), `Driver.run` L309-328, `start_caffeinate` L208-217, `run_step` L254-284 (`current-step.json`), `command_status` L378-388.

Test Evidence:
`.harness-dev/test-implement-loop.py::test_start_detaches_driver_and_status_reports_it` (asserts own session leader, caffeinate parented by driver with `-w <pid>`, step in own session, status output). Re-run OK.

Result:
PASS

Acceptance Criterion:
M1-AC3 `stop` terminates the running step (SIGTERM, then SIGKILL after grace) and the driver, clears the pid file, leaves committed work and `loop.log` in place, and produces exactly one stop notification.

Implementation Evidence:
`command_stop` L391-406; `Driver.terminate_step` L229-252 (killpg SIGTERM, grace loop, SIGKILL); `finish` L286-307 (single notification guarded by `notified`, pid file removed only if own pid).

Test Evidence:
`test_stop_ends_step_and_driver_leaving_log_and_git_untouched`, `test_stop_kills_step_that_ignores_sigterm_after_grace` (HEAD/porcelain unchanged, one notification, caffeinate gone, SIGKILL logged, grace honoured). Re-run OK.

Result:
PASS

Acceptance Criterion:
M1-AC4 `stop` and `status` with no driver, or with a stale pid file whose process is gone, print "not running" and exit 0.

Implementation Evidence:
`is_driver` L131-144 (liveness plus command-line identity check against pid reuse), `running_driver` L167-175 (removes stale pid file); `command_status`/`command_stop` early returns.

Test Evidence:
`test_status_and_stop_report_not_running_without_live_driver` (no file, dead pid, foreign live pid). Re-run OK.

Result:
PASS

Acceptance Criterion:
M1-AC5 `loop.log` records each step started (time, milestone, attempt), its outcome, each notification and whether sent, and the final outcome; every child logged with pid and command line, prompt by length only; nothing under `.harness/loop/` staged by `git add .harness`.

Implementation Evidence:
`log` L60-63, `record_command` L66-69, `describe_command` L72-80, `Driver.spawn` L202-206, `notify` L110-120, `finish` L297, `.gitignore` `*` written at L343.

Test Evidence:
`test_loop_log_records_step_lifecycle_with_timestamps`, `test_loop_log_records_unsent_notification_without_notify_file`, `test_commands_log_records_children_with_prompt_by_length`, `test_git_add_stages_fixture_changes_but_never_loop_state`. Re-run OK.

Result:
PASS

## Findings

### F1

Severity:
IMPORTANT

Problem:
The project's whole test suite is not green: `.harness-dev/test-orchestrator-inventory.py` `test_core_stays_compact` fails because `agents/orchestrator.md` is 730 lines against a 720-line cap. The failure is pre-existing — the file is 730 lines at baseline 5eccdcc and at HEAD, and `agents/` is not touched by the M1 diff — but the M1 evidence does not record it, so the milestone's validation record currently implies a clean suite.

Evidence:
`.harness/evidence/M1-review.log` ("Review retry 3" whole-suite run; "Review retry 4": `orchestrator.md lines HEAD: 730 baseline: 730`, `git diff --stat 5eccdcc HEAD -- agents` empty); `.harness/milestones.md` M1 `### Validation` / `### Follow-ups`.

Why it matters:
A red suite with no recorded explanation cannot be told apart from a regression by the completion gate or a later reviewer; the milestone record must say which non-passing result is known and why it is not M1's.

Suggested correction:
In `.harness/milestones.md` M1 (Validation or Follow-ups), record that `test-orchestrator-inventory.py::test_core_stays_compact` fails pre-existing at baseline 5eccdcc (730 > 720 lines in `agents/orchestrator.md`), is outside M1's diff, and is to be fixed separately. No production change in M1.

### F2

Severity:
OPTIONAL

Problem:
The M1 Follow-ups line says "`step N outcome:` is logged on the normal path only". `Driver.run` logs `step 1 outcome: <outcome>` immediately after `run_step` returns on both the normal and the stop path; only the stop-before-step-start path skips it.

Evidence:
`scripts/implement-loop.py` L320-322; `.harness/milestones.md` M1 `### Follow-ups` bullet 2.

Why it matters:
The written record misdescribes the logging behaviour that M1-AC5 depends on.

Suggested correction:
Reword the follow-up: the per-step outcome line is logged whenever a step ran (including when stopped mid-run); it is absent only when stop arrives before the step starts.
