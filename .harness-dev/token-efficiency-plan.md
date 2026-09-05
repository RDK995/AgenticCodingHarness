# Token-Efficiency and Accuracy Improvement Plan

Status: IMPLEMENTED ON BRANCH — authenticated regression and field release gates pending

Baseline: restored stable harness on `main` (`956a71a`; functional content from
`1f15d4d` / PR #21)

## Objective

Reduce token traffic and prevent runaway agent sessions while preserving the
task-level verification and milestone-level independent review that found real
defects during the phoneToLocalModel M16 run.

This plan deliberately removes the overall project-level review. Every milestone
keeps its independent review gate, but after the final milestone reaches `DONE`
the harness reports completion and stops. It does not dispatch a project-wide
reviewer, project-wide fix cycle, or automatic project-wide validation rerun.

## Baseline and success measures

The comparison dataset is the 19 measured milestone groups run with this harness
version, from the post-`1f15d4d` M1 run through M16. M12c was deferred, M14 was
not run, and M17 used the reverted B28-B32 harness and is excluded.

- 12,574 deduplicated API turns.
- 647.6 million tokens of traffic.
- Approximately $816 at the measurement script's configured prices.
- M16 alone: 154.2 million tokens and approximately $233.41.
- M16 parent context peak: 317,951 tokens.
- About 70% of measured stable-harness orchestrator invocations exceeded the
  stated 20-turn handoff point.

The initial release gates for this work are:

- Zero foreground polling violations.
- Zero agents exceeding their enforced hard limit.
- Orchestrator median handoff no higher than 22 turns.
- No worker over 45 turns without an explicit human-authorised exception.
- No semantic reviewer invocation for a record-only correction.
- Parent/controller traffic no more than 15% of milestone token traffic on the
  representative field runs.
- No regression in the existing behavioural fixtures.
- Every production change continues to receive independent verification and
  every milestone continues to receive an independent review.

## Target workflow

```text
plan milestone
  -> split if operationally oversized
  -> create acceptance and task packets
  -> implement bounded tasks
  -> commit each accepted task
  -> independently verify each task
  -> run milestone validation once
  -> independent milestone review
  -> record per-milestone as-built state
  -> DONE

all milestones DONE
  -> report completed milestones, evidence and unresolved follow-ups
  -> stop
```

There is no final project reviewer, project-wide fix cycle, composed drift review,
or final project-wide test rerun. Integration is checked incrementally: a
milestone reviewer examines its acceptance criteria plus any previously completed
interfaces touched by the current milestone's diff.

## Implementation order

The work is divided into six batches and ten independently committable work
packages. Packages are implemented in the numbered order unless a dependency
below explicitly allows parallel work. Each package receives its own commit and
must pass its named regression fixtures before the next batch begins.

## Batch 1 - Runtime safety

### P1 - Enforce hard agent limits and prohibit polling

Status: IMPLEMENTED — deterministic tests pass; live Claude fixture pending authentication

Dependencies: none

Changes:

1. Add runtime-enforced turn limits to every custom agent, starting with:
   - navigator: 10
   - orchestrator: 30
   - worker: 40
   - verifier: 35
   - reviewer: 50
   - as-built: 30
2. Confirm the installed Claude Code version's `maxTurns` and partial-result
   behaviour before making the limits authoritative.
3. Define one structured `CONTINUE`/`PARTIAL` envelope containing completed work,
   remaining work, current commit and artifact paths.
4. Add a plugin `PreToolUse` hook that blocks unbounded `sleep`, shell
   `until`/`while` polling, and repeated identical wait commands.
5. Permit only a single bounded readiness check with an explicit timeout and
   termination condition.
6. Disable background agents by default. Any exception must be explicit in the
   task packet and must not be polled by another agent.

Validation:

- Add a fixture in which an agent attempts to poll indefinitely; the hook must
  block it.
- Add a fixture in which a worker reaches its cap and returns resumable state.
- Re-run `fixtures/02-loop-cap`.

Acceptance criteria:

- [x] Every bundled subagent declares its tested hard limit and foreground mode.
- [x] The hook rejects foreground sleep/poll loops in eight black-box cases.
- [ ] A capped task resumes in a fresh context without losing accepted work.
- [ ] The existing two-cycle escalation still behaves as specified.

Implementation record, 2026-09-03:

- Added `maxTurns` and `background: false` to all six subagents.
- Added proactive handoff thresholds below every hard ceiling and fail-closed
  handling for an interrupted/malformed agent return.
- Added `hooks/hooks.json` and `scripts/guard-bash.py`; the hook rejects shell
  sleeps, `while`/`until` polling, unbounded curl calls and a repeated identical
  readiness check, while allowing ordinary repeated validation.
- `.harness-dev/test-guard-bash.py`: 8 tests pass.
- `.harness-dev/test-agent-guards.py`: 3 tests pass.
- The installed Claude Code 2.1.236 binary contains the `maxTurns` and current
  `hookSpecificOutput` contracts. A bounded live plugin probe could not reach
  model execution because this CLI installation is not logged in; it spent zero
  tokens and reported `Not logged in · Please run /login`. The two live
  acceptance criteria remain deliberately open.

## Batch 2 - Durable change boundaries

### P2 - Commit every accepted task

Status: IMPLEMENTED — static tests pass; historical live fixtures passed, re-run pending authentication

Dependencies: P1

Changes:

1. Create a milestone branch before implementation begins.
2. If relevant pre-existing changes are present, preserve them on that branch in
   a dedicated baseline commit only when their ownership and scope are clear.
3. Commit each accepted task by explicit file path after its verifier passes.
4. Record the milestone baseline, task commit, correction-cycle starting commit
   and final milestone commit in harness state.
5. Replace throwaway index trees, patch files and untracked-file reconstruction
   with ordinary commit ranges.
6. Never push, merge, rebase, stash, amend user history or delete branches.
7. A non-git target records that fact and uses the existing non-git fallback.

Validation:

- Update fixtures 09-12 to review real commit ranges.
- Add dirty-tree and newly-created-untracked-file cases.
- Falsify the implementation by removing a task commit and confirm the gate
  fails.

Acceptance criteria:

- [x] The runtime contract requires every accepted task to have a resolvable commit.
- [x] Verifiers inspect uncommitted and untracked output before it is accepted.
- [x] A failed task is explicitly forbidden from producing an accepted-work commit.
- [x] The snapshot/index-tree and patch-file mechanism is removed.

Implementation record, 2026-09-03:

- Selectively backported the previously fixture-validated B31 commit discipline;
  unrelated B28-B30 runtime changes were not imported.
- Milestones open a branch, accepted tasks and corrections are committed by
  explicit path, and correction review uses `git diff <Pre-correction> HEAD`.
- Tightened the earlier B31 behaviour: dirty source is committed as baseline
  only after ownership and scope are clear; ambiguity stops for the human.
- Removed automatic squashing as well as push, merge, rebase, stash and history
  rewriting. Independently verified task commits remain intact.
- `.harness-dev/test-commit-discipline.py`: 5 tests pass. The original B31
  implementation passed live fixtures `05` twice, `11` and `12`; re-running
  those fixtures on this branch requires an authenticated Claude CLI.

## Batch 3 - State and review architecture

### P3 - Introduce compact structured state

Status: IMPLEMENTED — schema, migration and deterministic checks pass locally

Dependencies: P2

Changes:

1. Keep `.harness/milestones.md` as a compact human-facing index.
2. Store operational state in versioned structured files, initially:
   - `.harness/state.json`
   - `.harness/tasks/<id>.json`
   - `.harness/reviews/<id>.json`
   - `.harness/evidence/<id>.json`
3. Give every milestone, task, criterion and finding a stable ID.
4. Reference commit hashes, symbols and artifact paths rather than mutable line
   numbers.
5. Define schemas and a compatibility version.
6. Provide a deterministic migration from existing Markdown-only state.
7. Keep narrative reports in separate Markdown artifacts where they improve
   human readability; they are not authoritative workflow state.

Validation:

- Resume a fixture entirely from structured state in a fresh session.
- Detect disagreement between the index and authoritative state.
- Migrate an old fixture without losing evidence or review-cycle information.
- Archive a completed milestone without breaking lookup.

Acceptance criteria:

- [x] The current milestone is located with one small state read.
- [x] State validation detects stale status, evidence and review-cycle data.
- [x] No agent must read the full historical milestone narrative to resume.
- [x] Existing projects have a deterministic migration command.

Implementation record, 2026-09-03:

- Added schema-v1 `.harness/state.json` shape, stable requirement/criterion ids,
  artifact lists and `current_milestone`; `examples/state.example.json` is the
  canonical example.
- Added `scripts/migrate-state.py` for existing Markdown boards and
  `scripts/check-state.py` for schema, index, artifact, review-cap, finding,
  criterion and all-DONE validation.
- Planning writes both views; every transition validates them; resume reads the
  small authoritative state then only the current Markdown section.
- `.harness-dev/test-state.py`: 8 tests pass, including migration, mismatch,
  review override, all-DONE and substantive-change rejection.

### P4 - Separate substantive review from record linting

Status: IMPLEMENTED — deterministic record-only gate and routing tests pass

Dependencies: P3

Changes:

1. Add a deterministic milestone checker covering:
   - acceptance criteria versus reviewer rows
   - unresolved `BLOCKER` and `IMPORTANT` finding IDs
   - commit and artifact existence
   - state/index consistency
   - validation ownership
   - review-cycle counts
2. Invoke the semantic reviewer only when production code, tests, requirements
   or architecture changed.
3. Send record-only corrections through the checker without another reviewer,
   full-suite run or live proof.
4. Enforce the two-cycle substantive review cap mechanically.
5. Permit a human to authorise one specifically named extra cycle. An override
   is not an unlimited loop and must be recorded in structured state.

Validation:

- A stale evidence path fails mechanically without invoking a reviewer.
- A production correction still receives a fresh independent review.
- A record-only correction cannot start broad validation.
- Deliberately mismatched cycle counts are rejected.

Acceptance criteria:

- [x] Record-only corrections consume zero additional semantic reviewer invocations.
- [x] Every substantive milestone correction remains independently reviewed.
- [x] Review caps cannot be bypassed with inconsistent state or counters.

Implementation record, 2026-09-03:

- Reviewer envelopes classify findings as `SUBSTANTIVE` or `RECORD_ONLY`; mixed
  findings are always substantive.
- Record-only correction accepts only `.harness/` diffs, runs the state checker,
  and cannot dispatch workers, orchestrators, reviewers or broad validation.
- Review cycles above two require a named human override in structured state.
- The black-box state tests falsify the record-only claim with a source change
  and confirm that the checker rejects it.

### P5 - Remove the overall project-level review

Status: IMPLEMENTED — static workflow tests pass; golden-path live run pending authentication

Dependencies: P3, P4

Changes:

1. Remove `Final fresh review` and its loop from `skills/implement/SKILL.md`.
2. Remove final-review mode from `agents/reviewer.md`.
3. Remove final-review fix-cycle routing from `agents/orchestrator.md` and
   `agents/references/fix-cycle.md`.
4. Remove automatic as-built `COMPOSE` mode if its only consumer is the deleted
   final review. Retain per-milestone as-built records.
5. Update README, runtime contract, examples and fixtures so that the final
   milestone's passing review is the last quality gate.
6. When every milestone is `DONE`, return only:
   - completed milestone IDs
   - validation and review artifact paths
   - unresolved follow-ups and known limitations
   - branch and commit information

Accuracy safeguard:

Each milestone reviewer checks integration with earlier milestones only when the
current diff changes one of their interfaces. Cross-milestone requirements must
be assigned to a concrete milestone acceptance criterion rather than deferred to
a final review.

Validation:

- Update `fixtures/05-golden-path` to stop after its milestone reaches `DONE`.
- Retarget `fixtures/10-as-built-drift` to per-milestone recording only, or
  remove its compose case if it has no remaining consumer.
- Confirm no final reviewer or final-review correction agent is dispatched.

Acceptance criteria:

- [x] All-DONE state terminates the workflow immediately after reporting.
- [x] No project-wide reviewer, fix cycle, drift review or validation rerun is
  invoked.
- [x] The workflow cannot finish while the last milestone's own gate is open.
- [x] Cross-milestone integration affected by a diff remains in that
  milestone's review scope.

Implementation record, 2026-09-03:

- Removed final-review mode, the project-level correction loop, automatic
  as-built compose mode and the `drift.md` artifact.
- All-DONE now performs a deterministic ownership/status/finding check, reports
  milestone artifacts and stops without another reviewer or broad test run.
- Milestone review inputs now include existing consumers and focused integration
  checks for interfaces changed by the current diff.
- Updated README, runtime documentation, MVP expansion instructions and fixtures
  `05` and `10` to the milestone-terminal workflow.
- `.harness-dev/test-no-project-review.py`: 4 tests pass. Live golden-path proof
  remains pending an authenticated Claude CLI.

## Batch 4 - Context reduction

### P6 - Reduce the parent/controller context

Status: IMPLEMENTED — static contract tests pass; field measurement pending

Dependencies: P3, P4, P5

Changes:

1. Make reviewers write reports directly to their artifact path.
2. Reviewer returns only verdict, report path, criterion statuses and finding
   IDs.
3. Worker and verifier return compact structured envelopes plus artifact paths.
4. Remove the instruction that makes the skill session reproduce reviewer
   reports verbatim.
5. Forbid the controller from reading source code, full logs, full reports or
   implementation discussions.
6. Stop an implementation invocation when requirements change or another
   milestone becomes the active subject; resume in a fresh context.

Validation:

- Seed a large reviewer report and confirm only its envelope reaches the
  controller.
- Confirm a fix orchestrator can work from the report path and finding IDs.
- Confirm the completion gate works entirely from structured fields.

Acceptance criteria:

- [x] Controller instructions forbid duplicated report bodies.
- [ ] Representative fixture parent context remains below 100,000 tokens.
- [x] The controller is restricted to dispatch and mechanical gates.

Implementation record, 2026-09-03:

- Reviewer now owns the full `CHANGES REQUIRED` artifact and has `Write` solely
  for the supplied `.harness/reviews/` path.
- Reviewer returns verdict, report path, criterion statuses, finding counts and
  terminal result; a passing review writes no artifact.
- The skill validates the compact envelope and passes only the artifact path to
  a correction orchestrator. It may not read, quote or reproduce the report.
- `.harness-dev/test-compact-returns.py`: 4 tests pass.
- The sub-100k field criterion remains open until an authenticated fixture or
  real milestone can be measured.

### P7 - Assign validation ownership and compress output

Status: IMPLEMENTED — static ownership tests pass; duplicate-run telemetry pending P10

Dependencies: P2, P3, P6

Changes:

1. Worker owns focused task tests.
2. Verifier independently checks task behaviour and its committed diff.
3. Reviewer owns milestone acceptance and affected-interface integration tests.
4. Orchestrator does not run tests except to resolve contradictory evidence.
5. Store full command output in evidence artifacts and return command, exit
   status, concise summary and failures only.
6. Run broad baseline checks such as type-checking once per milestone, and again
   only if relevant files change afterward.
7. Track the commit against which every validation artifact was produced.

Validation:

- Detect duplicate broad-suite execution against an unchanged commit.
- Confirm full failure detail remains available from the artifact path.
- Re-run `fixtures/09-vacuous-pass` to ensure irrelevant green commands remain
  unacceptable.

Acceptance criteria:

- [x] Runtime ownership prevents several roles from broad-testing an unchanged commit.
- [x] Full output is retained in evidence artifacts while failures stay inline.
- [x] Verifier and reviewer independence remains intact.

Implementation record, 2026-09-03:

- Workers own focused task validation, verifiers independently rerun that task
  command, and reviewers own milestone acceptance plus affected-interface checks.
- Orchestrators record commands and judge evidence but run tests only when two
  artifacts contradict each other.
- Complete output is stored under `.harness/evidence/`, keyed by task/milestone
  and commit; return envelopes contain only status, summary and failures.
- `.harness-dev/test-validation-ownership.py`: 4 tests pass. P10 still needs to
  add transcript detection for duplicate commands, and live behaviour remains
  part of the authenticated field run.

## Batch 5 - Work sizing and model routing

### P8 - Split milestones using operational complexity

Status: IMPLEMENTED — operational split rules and M16-shaped fixture added

Dependencies: P3, P7

Changes:

1. Add pre-implementation split signals for:
   - more than three affected subsystems
   - concurrency or lifecycle ownership changes
   - live-environment proof combined with implementation
   - more than roughly eight expected production files
   - more than six anticipated worker tasks
   - multiple independently demonstrable outcomes
2. Record which signal caused every split.
3. Split before acceptance work or implementation tasks are created.
4. Require every resulting milestone to be an independently useful vertical
   slice with an observable result.

Validation:

- Add an M16-shaped fixture containing few criteria but several lifecycle and
  concurrency responsibilities.
- Confirm it splits before implementation.
- Confirm a small coherent cross-file change is not split unnecessarily.

Acceptance criteria:

- [x] The M16-shaped fixture cannot enter implementation as one milestone.
- [x] Each child milestone has its own observable outcome and review boundary.
- [x] Criterion count is not the sole sizing signal.

Implementation record, 2026-09-04:

- Added six named operational-complexity signals alongside criterion count and
  vertical-slice shape.
- Two signals, or concurrency/lifecycle work combined with live proof, force a
  split before task packets or implementation; one signal forces an explicit
  seam check.
- Split reasons are persisted in structured state and the human milestone view.
- Fixture `13-operationally-oversized` represents the M16 failure shape, while
  static tests protect coherent small cross-file changes from needless splits.

### P9 - Route models by current task and review scope

Status: IMPLEMENTED — current-diff routing and structured reasons enforced

Dependencies: P4, P7, P8

Changes:

1. Use Haiku for navigation, mechanical state edits and bounded low-risk work.
2. Use Sonnet for ordinary implementation, verification and substantive
   correction review.
3. Use Opus for architecture, security, difficult concurrency and explicitly
   justified high-risk work.
4. A record-only correction invokes no reviewer and inherits no historical tier.
5. A milestone review's tier is based on the highest-risk material changed since
   the previous review, not the highest tier ever used in the milestone.
6. Record every Sonnet-to-Opus routing reason in structured state.

Validation:

- A mechanical task routes to Haiku.
- A concurrency-sensitive task routes to Opus with a recorded reason.
- A narrow Sonnet correction following an earlier Opus task remains Sonnet.
- A record-only correction invokes no reviewer.

Acceptance criteria:

- [x] Every elevated routing has a machine-readable reason.
- [x] One historical high-risk task cannot permanently elevate a milestone.
- [ ] Existing accuracy fixtures pass at the revised routing levels.

Implementation record, 2026-09-04:

- Haiku handles navigation, mechanical edits and bounded low-risk tasks; ordinary
  implementation starts at Sonnet; structural, security and difficult
  concurrency work starts at Opus.
- Task state records tier, model, reason code and detail; the state checker
  rejects malformed routing and unnamed Top-tier elevation.
- Review tier is derived from substantive work in the current diff. Cycle-2
  corrections cannot inherit an older cycle's Opus tier, and record-only changes
  dispatch no semantic reviewer.
- Static routing tests pass. Authenticated accuracy fixtures remain pending.

## Batch 6 - Prompt and release optimisation

### P10 - Trim prompts, stabilise caching and add regression gates

Status: IMPLEMENTED — prompt and automated telemetry complete; field pilots pending

Dependencies: P1-P9

Changes:

1. Reduce `agents/orchestrator.md` to approximately 600-700 lines.
2. Move slow-path instructions into targeted references.
3. Keep delegation, cap handling, verification judgement and commit discipline
   in the always-loaded core.
4. Remove historical measurements and duplicated rationale from runtime prompts;
   retain them in this development record.
5. Put stable reusable instructions before volatile milestone data.
6. Extend transcript measurement to report:
   - token traffic and estimated cost by role and milestone
   - peak context and API turns
   - polling and repeated commands
   - parent/controller share
   - duplicate validation commands
   - semantic reviews per substantive diff
   - harness commit/version
7. Add an automated release check for the success measures at the top of this
   plan.

Validation:

- Inventory rules before and after trimming; every removed runtime line must be
  rationale or duplication, not a behavioural rule.
- Run fixtures 02, 03, 05, 09, 10, 11 and 12 after every affected batch.
- Run the full fixture suite before merge.
- Pilot on one medium real milestone, then one M16-shaped milestone.
- Compare both against the 647.6-million-token baseline and the M16 tail.

Acceptance criteria:

- [x] Orchestrator core is no more than approximately 700 lines with no lost
  behavioural rule.
- [ ] All authenticated fixtures pass.
- [x] Automated reporting includes every named efficiency and accuracy metric.
- [ ] Field pilots meet the release gates or the change remains unmerged with
  the failed measurement recorded.

Implementation record, 2026-09-04:

- Reduced the always-loaded orchestrator from 841 to 692 lines by removing
  historical measurements and duplicated rationale while retaining dispatch,
  split, routing, retry, verification-judgment, commit and handoff rules.
- Rebuilt `measure-context.py` around message-id deduplication and JSON output.
  It reports token/cost by role and milestone, peak context/API turns, polling,
  repeated commands, parent share, duplicate validation, semantic review/diff
  counts, and harness version/commit.
- Added `check-efficiency.py`, which fails the quantitative release thresholds
  and requires explicit fixture, verification and milestone-review evidence.
- Local static and synthetic transcript tests pass. Authenticated fixtures and
  the two real field pilots remain required before merge.

## Regression suite

The minimum regression set after every batch is:

- `fixtures/02-loop-cap`: bounded correction cycles and escalation.
- `fixtures/03-drift-undeclared`: architectural deviation is not silently
  accepted.
- `fixtures/05-golden-path`: normal implementation reaches milestone `DONE`.
- `fixtures/09-vacuous-pass`: green but irrelevant validation is rejected.
- `fixtures/10-as-built-drift`: per-milestone as-built recording, retargeted away
  from project-level compose review.
- `fixtures/11-correction-wandered`: correction scope cannot silently widen.
- `fixtures/12-scoped-second-review`: subsequent review sees the correct diff.

New fixtures introduced by this plan cover hard caps and polling, commit
discipline, structured-state migration, record-only correction, compact agent
returns, validation ownership and M16-shaped splitting.

## Rollout and merge policy

1. Work from a new branch based on the restored stable `main`.
2. Implement one numbered package per commit.
3. Use the reverted B28-B32 branch only as source material; do not cherry-pick
   the full merge or assume its changes remain correct under this plan.
4. Run the minimum regression set after each batch and the complete suite before
   merge.
5. Make one behavioural change at a time when field-measuring so attribution is
   possible.
6. Do not merge on cost alone. A package must preserve or improve the accuracy
   fixtures associated with the behaviour it changes.
7. Do not reintroduce an overall project-level review during implementation. If
   a missing cross-project check is discovered, assign it to a concrete
   milestone acceptance criterion or add a deterministic gate.

## Completion definition

This plan is complete when P1-P10 are accepted, the full fixture suite passes,
both field pilots satisfy the release gates, and an all-DONE project terminates
without dispatching any overall project-level reviewer or fix cycle.
