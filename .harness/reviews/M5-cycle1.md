# M5 review — cycle 1

Verdict: CHANGES REQUIRED (Scope: RECORD_ONLY)

Diff: git diff 76ba78510cc492d0fed1e3aaa9f50ffbf3243422 HEAD (m5-ntfy-notifications). Validation re-run by reviewer: python3 .harness-dev/test-implement-loop.py — 72 tests OK (65s); every other .harness-dev/test-*.py run once — all OK except test-orchestrator-inventory.py (1 pre-existing failure). Full output: .harness/evidence/M5-review.log

## Acceptance criteria

Acceptance Criterion: M5-AC1 start/stop with alert config path sends stop notification via ntfy, config read at send time, POST to <server>/<topic> on local stub; no external network.
Implementation Evidence: scripts/implement-loop.py ntfy_sink (reads Path(path) inside attempt on every send; POST server.rstrip('/')+'/'+topic), choose_sink default -> ntfy_sink, alert_config_path, --alert-config, config.json alert_config.
Test Evidence: test_stop_notification_is_posted_to_ntfy_reading_the_config_at_send_time (topic swapped after start; stub records /second and exact body); test_alert_config_path_comes_from_option_then_env_then_default; test_sink_posts_the_body_and_reports_status_only; run_loop forces HARNESS_LOOP_ALERT_CONFIG to a temp path for every subprocess; in-process notify test patches choose_sink.
Result: PASS

Acceptance Criterion: M5-AC2 topic never in stdout, stderr, loop.log, commands.log, outcome.json, or error/exception text incl. failed POST.
Implementation Evidence: ntfy_sink reasons built from fixed text/status code/class name only; NotSent raised outside except with `from None`; final replace guard; not_sent_reason.
Test Evidence: test_topic_never_appears_in_output_or_loop_files (200/500/403/dead port, all 4 command outputs + 4 loop files); test_sink_failure_reason_never_carries_the_topic (7 exception kinds incl. class named after topic; chain length 1; traceback text; loop.log); test_refused_start_posts_to_ntfy_or_says_why_not_without_the_topic.
Result: PASS

Acceptance Criterion: M5-AC3 missing/invalid config, network failure, HTTP error -> loop.log "not sent" with reason, loop keeps running.
Implementation Evidence: config_problem; ntfy_sink except branches; notify catches Exception and logs "notification not sent: <reason>: <message>"; refuse prints reason on stderr.
Test Evidence: test_failed_ntfy_send_is_logged_and_the_driver_still_finishes (8 cases; outcome finished; final lines); test_without_notify_file_missing_alert_config_records_unsent_notification; test_refused_start_... (403 and missing).
Result: PASS

Acceptance Criterion: M5-AC4 every message names the project; >4096-byte body truncated with visible marker.
Implementation Evidence: prepare_message applied in notify (all driver notifications) and refuse (the only two send paths); NTFY_LIMIT=4096, TRUNCATED_MARK.
Test Evidence: test_stop_notification_names_the_project; test_refused_start_notification_names_the_project; stop body equality in AC1 test (ntfy path labelled); test_prepare_message_* (ascii, multibyte boundary); test_a_labelled_message_of_exactly_the_limit_is_not_truncated.
Result: PASS

## Findings

F1
Severity: IMPORTANT
Problem: The whole-suite run is not green: .harness-dev/test-orchestrator-inventory.py::test_core_stays_compact fails (agents/orchestrator.md 730 lines > 720 cap). Pre-existing (fails identically at baseline 76ba785; M5 diff does not touch agents/ or that test), and accepted as permitted pre-existing in M1/M2/M3 records, but M5's record (milestones.md ### Validation, state.json milestones.M5.validation) lists only test-implement-loop.py as PASS and does not record this non-passing result as permitted.
Evidence: .harness/evidence/M5-review.log; .harness/state.json milestones.M5.validation; .harness/milestones.md M5 ### Validation
Why it matters: The completion gate requires validation to pass or any non-passing result to be explicitly permitted; without a record, M5 would be marked DONE over an unacknowledged red suite.
Suggested correction: Record-only: add to M5 validation/follow-ups in milestones.md and state.json that the full suite was run, test_core_stays_compact fails pre-existing (730 > 720, present at baseline 76ba785, untouched by M5) and is accepted as permitted for M5's gate, as was done for M2. Do not fix orchestrator.md inside M5 (scope).

F2
Severity: OPTIONAL
Problem: The stop command waits grace + STOP_EXTRA_WAIT (10s) for the driver to exit, but on stop the driver may first spend up to the step's grace terminating it and then up to NTFY_TIMEOUT (10s per socket op, DNS not bounded) POSTing the stop notification. A slow/hung ntfy server can make `stop` print "did not exit within ..." and return 1 although the driver finishes correctly.
Evidence: scripts/implement-loop.py NTFY_TIMEOUT=10, STOP_EXTRA_WAIT=10.0, command_stop limit; Driver.finish -> notify
Why it matters: Misleading owner-facing stop result in an edge case; no data loss.
Suggested correction: Either make STOP_EXTRA_WAIT exceed NTFY_TIMEOUT with margin (e.g. NTFY_TIMEOUT + 5), or lower NTFY_TIMEOUT; record as follow-up if not fixed now.
