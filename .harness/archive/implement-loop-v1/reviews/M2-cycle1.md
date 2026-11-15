# M2 cycle 1 review (partial)

## Acceptance criteria

Acceptance Criterion: M2-AC1 successive fresh claude processes, one per step, in project dir, each /harness:implement, judged from state.json/milestones.md
Implementation Evidence: scripts/implement-loop.py Driver.run (itertools.count loop), take_snapshot, judge_step, run_step (cwd=self.project, session_command(claude, STEP_PROMPT))
Test Evidence: test_loop_runs_successive_fresh_steps_until_every_milestone_is_done (4 runs, 4 pids, cwd, -p /harness:implement); test_state_not_output_decides_the_step_result; test_nonzero_exit_with_state_advanced_to_all_done_is_finished
Result: PASS

Acceptance Criterion: M2-AC2 phase boundary with progress continues; all DONE stops as finished
Implementation Evidence: judge_step PROGRESS / FINISHED; Driver.run breaks on non-PROGRESS
Test Evidence: same 4-step test (M1 REVIEW -> progress -> step 2); test_milestones_file_only_change_counts_as_progress; test_judge_step_branches
Result: PASS

Acceptance Criterion: M2-AC3 bypassPermissions, deny-prompt setting, --plugin-dir, deny rules in --disallowedTools and --settings permissions.deny; driver runs no push/merge
Implementation Evidence: session_command + DENY_RULES; `--permission-prompts none` confirmed against installed `claude --help` ("anything that would prompt is denied automatically"); HARNESS_ROOT has .claude-plugin/plugin.json
Test Evidence: test_builder_returns_locked_down_command; test_step_runs_locked_down_with_minimal_environment; test_driver_source_runs_no_push_or_merge
Result: PASS (rule coverage gaps reported as finding F1)

Acceptance Criterion: M2-AC4 only allowed env names; fake secret absent from child env, commands.log, loop.log
Implementation Evidence: SESSION_ENV_NAMES filter in session_command; env passed to spawn
Test Evidence: test_step_runs_locked_down_with_minimal_environment; test_parent_secret_reaches_neither_step_nor_logs
Result: PASS

Acceptance Criterion: M2-AC5 step over limit (3h default, overridable) terminated, killed after grace, logged as failed step
Implementation Evidence: run_step deadline + terminate_step; judge_step timed_out branch; --step-timeout option persisted to config.json
Test Evidence: test_step_over_time_limit_is_terminated_and_recorded_as_failed; test_step_over_time_limit_ignoring_sigterm_is_killed_after_grace (both use --step-timeout 1, proving override); test_timed_out_step_is_failed_even_if_state_advanced; test_step_timeout_defaults_to_three_hours_and_is_listed_in_help
Result: PASS

## Findings
F1 IMPORTANT deny-list gaps (branch -m/-M, checkout -B, switch -C, reset --soft/--mixed/HEAD~, commit ... --amend) - scripts/implement-loop.py DENY_RULES
F2 IMPORTANT whole suite red: .harness-dev/test-orchestrator-inventory.py test_core_stays_compact (730 > 720), pre-existing at baseline 8c67645
F3 OPTIONAL --step-timeout accepts <=0 / nan

## Findings (full detail)

Severity: IMPORTANT
Problem: F1. The deny list misses common, direct forms of committing on main and rewriting history, which FR11 says it blocks. Because the rules match on prefixes, these get through: `git branch -m main` / `git branch -M main` (renames the milestone branch to main); `git checkout -B main`; `git switch -C main`; `git reset --soft HEAD~1`, `git reset --mixed HEAD~1`, `git reset HEAD~1`, `git reset --keep`; and `git commit -a --amend` / `git commit -m x --amend` (only a bare `git commit --amend` matches).
Evidence: scripts/implement-loop.py DENY_RULES (lines 50-71); .harness-dev/test-implement-loop.py REQUIRED_DENY checks only that the listed rules are present.
Why it matters: these rules are the only guard on an unattended session (the task was routed Top for SECURITY). M3's start gate checks the branch only once, before the first step. The existing follow-up covers only obfuscated variants (git -C, aliases), not these plain forms.
Suggested correction: add Bash(git branch -m:*), Bash(git branch -M:*), Bash(git branch --move:*), Bash(git branch --force:*), Bash(git checkout -B:*), Bash(git switch -C:*), Bash(git switch --force-create:*), Bash(git reset --soft:*), Bash(git reset --mixed:*), Bash(git reset --keep:*), Bash(git reset --merge:*), Bash(git reset HEAD~:*), Bash(git reset HEAD^:*), plus an amend rule that matches anywhere on the line (for example Bash(git commit * --amend*), once the CLI's wildcard syntax is confirmed). Leave plain `git reset <path>` allowed. Add the new rules to REQUIRED_DENY. Note in the follow-ups that the live M3-AC5/M7 check should try `git branch -m main` and `git commit -a --amend`.

Severity: IMPORTANT
Problem: F2. The whole suite is red: .harness-dev/test-orchestrator-inventory.py test_core_stays_compact fails with "730 not less than or equal to 720". The failure already exists at baseline 8c67645, and the diff does not touch agents/.
Evidence: .harness/evidence/M2-review.log; agents/orchestrator.md (730 lines, last changed in 94cfccd, before the baseline).
Why it matters: the completion gate needs validation to pass, or an explicit permission for any result that does not pass. An unrecorded red test hides later regressions in the same file.
Suggested correction: do not fix it inside M2. Either fix it in a separate commit (trim orchestrator.md to 720 lines or fewer, or deliberately raise the budget), or record in the M2 Follow-ups/Decisions (milestones.md + state.json) that this failure predates M2 and is accepted for M2's gate (record-only).

Severity: OPTIONAL
Problem: F3. --step-timeout accepts 0, negative numbers and nan. Zero or negative makes every step time out at once; nan makes the `>=` check always False, so steps never time out.
Evidence: scripts/implement-loop.py parse_args --step-timeout (type=float); run_step deadline.
Why it matters: a typo either fails the loop at once or silently removes the time limit.
Suggested correction: reject values that are not finite and positive in command_start (plain message, exit 2), and add one test.
