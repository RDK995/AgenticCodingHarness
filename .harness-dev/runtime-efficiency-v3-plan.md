# Harness Runtime Efficiency and Accuracy Plan (v3)

**Status:** READY FOR IMPLEMENTATION  
**Baseline:** `main` at `c516dd5`  
**Recommended branch:** `improvement/runtime-efficiency-v3`  
**Current local Claude Code:** `2.1.236`  
**Target runtime for live evals:** `>=2.1.269`  

## 1. Objective

Reduce accepted-milestone token cost and eliminate unbounded orchestrator/worker
contexts without weakening implementation or review accuracy.

The work is complete only when the new path:

1. preserves or improves the existing accuracy fixtures;
2. has no orchestrator context above the agreed hard limit;
3. returns foreground subagent results without notification/re-entry loops;
4. records state and review evidence truthfully;
5. measures real billable work rather than missing, duplicated, or misclassified
   sessions; and
6. demonstrates a lower median cost per accepted task in repeated A/B runs.

This plan deliberately excludes an overall project-level review. Milestones remain
the unit of implementation, independent review, acceptance, and measurement.

## 2. Why this revision is needed

The current harness resolved the worst pre-PR orchestrator behaviour, but it has
not yet demonstrated an end-to-end cost reduction:

- orchestrator traffic fell by about 31%, and the largest observed orchestrator
  context fell from 243k to 146k tokens;
- no post-PR orchestrator context exceeded 200k tokens;
- reviewer tokens per completed milestone fell by about 47%; but
- raw total tokens rose about 19% and estimated total cost rose about 50%;
- parent/skill sessions and Opus worker routing became the dominant costs;
- field runs still executed polling commands that should have been denied; and
- the state checker does not recognise the namespaced requirement and milestone
  IDs used by the real P2 project.

The principal remaining problem is therefore not prompt shortening in isolation.
It is runtime control: foreground execution, bounded parent context, economical
model routing, authoritative state transitions, and trustworthy telemetry.

## 3. Non-negotiable invariants

- Accuracy is a hard gate; cost improvements cannot compensate for a missed
  requirement, false PASS, or incomplete review.
- Every substantive implementation task still receives independent review.
- A milestone may become `DONE` only after its terminal review result is complete,
  bound to the reviewed `HEAD`, and covers every owned criterion.
- The requirements document and structured state must agree on complete
  requirement ownership before all-DONE can pass.
- Milestone and requirement IDs are opaque namespaced identifiers. Logic must not
  assume `M<digits>` or `FR<digits>`.
- The harness must not rely on deprecated `TaskOutput` behaviour once foreground
  agent execution has been proved on the supported runtime.
- No live or paid Claude evaluation runs without a separate, explicit user
  authorization naming the run and maximum spend.
- Zero-cost unit, parser, state, and fixture tests must run before any paid test.
- Existing `.harness` projects remain readable. Any state migration must be
  explicit, idempotent, backed up, and independently validated.
- Unrelated and private evaluation artifacts are never committed.

## 4. Delivery strategy

Implement four independently reviewable pull requests in order. Do not combine
runtime changes with model-routing changes: separating them makes regressions and
cost changes attributable.

The new controller is introduced through an opt-in `implement-v3` path. The
current `implement` skill remains the control until the behavioural campaign
passes. Promotion happens only after PR 4.

| PR | Purpose | Depends on | Main release gate |
|---|---|---|---|
| 1 | Truthful state and telemetry | None | Real P2 fixtures validate and empty telemetry fails closed |
| 2 | Foreground bounded runtime | PR 1 | Live foreground/hook probes pass; no notification re-entry |
| 3 | Economical, risk-aware routing | PR 2 | Routing fixtures pass with no loss of high-risk review coverage |
| 4 | Behavioural A/B and promotion | PRs 1-3 | Accuracy non-regression and lower median accepted-task cost |

---

## 5. PR 1 — Truthful state and telemetry

**Goal:** Make completion gates and efficiency reports trustworthy before using
them to judge the runtime changes.

### S1.1 — Parse namespaced identifiers

**Files**

- `scripts/requirements_ids.py`
- `scripts/check-state.py`
- `scripts/migrate-state.py`
- `.harness-dev/test-state.py`
- new fixtures under `.harness-dev/fixtures/state/`

**Changes**

- Extract requirement IDs from explicit Markdown anchors/labels without assuming
  an `FR` prefix. Support examples such as `FR1`, `P2-R10.19`, and future
  namespace forms containing letters, digits, dots, underscores, and hyphens.
- Treat the exact extracted string as the identifier; do not normalise case or
  punctuation silently.
- Match milestone headings and state keys as opaque IDs, including `P2-M7c`.
- Require the requirements document path for `--all-done` and compare its full ID
  set with the ownership map:
  - missing ownership is an error;
  - unknown ownership keys are an error;
  - duplicate definitions are an error;
  - ownership of an unknown milestone is an error.
- Preserve backward compatibility for simple `FR<n>` and `M<n>` projects.

**Tests**

- Simple IDs still parse.
- Namespaced P2 IDs parse exactly.
- Dotted IDs do not collapse into their prefixes.
- Duplicate, missing, and extra IDs fail with actionable messages.
- A representative OpenCode P2 state/requirements/milestones fixture passes.

**Acceptance**

- `check-state.py --all-done` can validate the representative P2 project.
- Removing any one P2 requirement from ownership makes it fail.

### S1.2 — Make review evidence authoritative

**Files**

- `agents/reviewer.md`
- `agents/orchestrator.md`
- `skills/implement/SKILL.md`
- new `scripts/check-review-result.py`
- new `.harness-dev/test-review-result.py`

**Changes**

- Define a compact terminal review-result JSON artifact with:
  - schema version;
  - milestone ID and review cycle;
  - base and reviewed `HEAD` commits;
  - complete criterion ID set and per-criterion result;
  - verdict (`PASS`, `CHANGES_REQUIRED`, or `BLOCKED`);
  - finding counts and finding IDs;
  - `complete: true` written only after all review work is finished.
- Require the reviewer to write the artifact atomically as its final tool action.
  Draft or partial files use a temporary name and are never authoritative.
- Validate schema, current `HEAD`, criterion-set equality, and verdict consistency
  before the controller consumes the result.
- Keep the textual return as a concise human summary, not the source of truth.
- A missing, partial, stale-HEAD, or criterion-incomplete artifact is an
  interrupted review and can never produce PASS.

**Tests**

- Complete PASS and CHANGES_REQUIRED artifacts validate.
- Truncated JSON, `complete: false`, stale `HEAD`, duplicate criteria, and missing
  criteria fail closed.
- A complete artifact remains usable if the final prose response is interrupted.
- A prose PASS without a valid artifact cannot advance state.

**Acceptance**

- Review completion is durable and small enough to return without replaying the
  reviewer transcript.
- The interruption policy distinguishes incomplete work from a response cut off
  after an already-complete terminal artifact.

### S1.3 — Enforce review/state transitions mechanically

**Files**

- new `scripts/transition-state.py`
- `scripts/check-state.py`
- `scripts/migrate-state.py`
- `skills/implement/SKILL.md`
- `agents/orchestrator.md`
- `.harness-dev/test-state.py`

**Commands to provide**

```text
transition-state.py enter-review --state <path> --milestone <id> --head <sha>
transition-state.py apply-review --state <path> --result <path>
transition-state.py reopen-after-review --state <path> --milestone <id>
transition-state.py finalize --state <path> --milestone <id> --head <sha>
```

**Changes**

- Use atomic file replacement and preserve a timestamped backup for migrations.
- `enter-review` records the current `HEAD` and requires all owned criteria to be
  defined. Criteria may not already be credited as PASS unless a valid terminal
  review at that same `HEAD` supports them.
- `apply-review` consumes only a validated terminal review result. PASS criteria
  become credited; failed criteria remain pending and reopen the milestone for a
  bounded fix cycle.
- `finalize` requires a complete PASS result for the same `HEAD`, every owned
  criterion PASS, required as-built evidence recorded, and Markdown/JSON status
  parity.
- `check-state.py` remains the independent validator and must not share all of its
  validation logic with the mutator.
- Accept legacy singular `review` records when reading, but write one documented
  canonical shape. Migration to the canonical shape is explicit and idempotent.

**Tests**

- Illegal transitions fail without modifying the state file.
- REVIEW cannot pre-credit criteria without valid same-HEAD review evidence.
- A stale review cannot finalize a milestone after a fix commit.
- Re-running a completed transition is either a documented no-op or a clear
  failure; it must never duplicate history.
- Migration creates a backup and repeated migration produces identical output.

**Acceptance**

- The M7c-style premature criterion credit is rejected.
- Every successful transition passes a fresh `check-state.py` invocation.

### S1.4 — Correct context and cost measurement

**Files**

- `.harness-dev/measure-context.py`
- `.harness-dev/check-efficiency.py`
- `.harness-dev/test-measure-context.py`
- `.harness-dev/test-guard-bash.py`
- new `.harness-dev/README.md`

**Changes**

- Write a measurement manifest containing source root, resolved paths, collection
  time, harness commit, runtime version, target project/milestone, fixture/run ID,
  arm, and completeness warnings.
- Separate at least these quantities:
  - context/input traffic;
  - output tokens;
  - cache reads and cache creation;
  - estimated billable cost;
  - parent/skill, orchestrator, navigator, worker, reviewer, verifier, and as-built
    roles.
- Detect duplicate sessions and expose included/excluded IDs with reasons.
- Align bounded-curl parsing with the Bash guard, including
  `--max-time=5`, `--max-time 5`, `-m5`, and `-m 5`.
- Classify a command as an executed polling violation only when execution evidence
  shows it was allowed. Record denied attempts separately.
- Make efficiency checking fail closed when:
  - zero contexts were measured;
  - required roles are absent for the selected test type;
  - provenance is incomplete;
  - parsing warnings make the report non-comparable.
- Report cost per accepted milestone/task in addition to aggregate cost.

**Tests**

- Empty and missing session roots fail the release gate.
- All supported curl timeout forms are non-polling.
- Unbounded curl, sleep loops, and repeated foreground status checks are polling.
- Denied attempts do not count as executed polling.
- Duplicate sessions are not double-counted.
- Raw traffic and estimated billable cost remain distinct.

**PR 1 exit gate**

```bash
for f in .harness-dev/test-*.py; do python3 "$f" || exit 1; done
claude plugin validate .
```

Additionally validate one anonymised real-state fixture and one historical
session fixture. This PR requires no paid model calls.

---

## 6. PR 2 — Foreground, bounded runtime and parent isolation

**Goal:** Remove the runtime behaviour that causes transcript re-entry and parent
context accumulation.

### S2.1 — Establish a supported runtime contract

**Files**

- new `scripts/runtime-preflight.py`
- `README.md`
- `.harness-dev/README.md`
- plugin/version metadata as appropriate
- new `.harness-dev/test-runtime-preflight.py`

**Changes**

- Record the supported Claude Code minimum version and fail with an actionable
  message below it.
- Split preflight into:
  - `--static`: zero-cost version, file, hook registration, and configuration
    checks;
  - `--live`: explicitly authorized model-backed behavioural probes.
- Verify the plugin is loaded from the intended checkout and report the exact
  commit/version used by the session.
- Do not upgrade the user's CLI automatically. Runtime upgrade is a documented,
  explicit checkpoint before live testing.

**Acceptance**

- The current `2.1.236` runtime is correctly reported as insufficient for the
  plugin-eval stage rather than silently skipping it.

### S2.2 — Prove hooks for parent and subagents

**Files**

- `hooks/hooks.json`
- `scripts/guard-bash.py`
- `scripts/runtime-preflight.py`
- `.harness-dev/test-guard-bash.py`

**Changes**

- Add safe audit events containing session/agent identity, rule ID, decision, and
  a command hash. Do not log raw commands or environment values.
- The live preflight asks both the parent and a spawned agent to attempt:
  - an allowed harmless command;
  - a denied sleep/polling command;
  - an allowed bounded curl syntax without making a network request.
- Confirm that denied tool calls never execute and that audit evidence is present
  for parent and child contexts.
- Abort a harness run before implementation if the guard is expected but inactive.

**Acceptance**

- Parent and child denial probes pass on the supported runtime.
- A missing hook fails preflight; it cannot degrade to a warning.

### S2.3 — Restore true foreground agent execution

**Files**

- new `agents/controller.md`
- new `skills/implement-v3/SKILL.md`
- new references under `skills/implement-v3/references/`
- `agents/orchestrator.md`
- `.harness-dev/test-compact-returns.py`
- new `.harness-dev/test-foreground-contract.py`

**Changes**

- Launch the v3 controller with background tasks disabled using the supported
  `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` runtime configuration.
- Require ordinary subagent calls to block and return their compact result in the
  initiating turn.
- Retain the existing `TaskOutput` compatibility path only until the live
  foreground probe passes. Remove it from v3 after proof; do not add new polling
  around a deprecated API.
- Define one compact return envelope shared by worker, navigator, verifier, and
  reviewer. Large evidence lives in bounded files; returns contain paths, hashes,
  result, and only the findings needed for the next decision.
- Reject unsolicited background agent IDs/notifications in v3 as a runtime
  contract failure.

**Tests**

- Static tests check the v3 contract semantically, not only by matching one prompt
  sentence.
- The live probe dispatches two concurrent harmless subagents and verifies that
  both results arrive without a later notification-driven re-entry.
- There are zero `sleep`, `TaskOutput`, or foreground polling calls in the session.

**Acceptance**

- Two concurrent agents complete and collect in one controller invocation.
- No agent transcript is replayed into the parent to discover completion.

### S2.4 — Isolate and bound the parent/controller context

**Files**

- `skills/implement-v3/SKILL.md`
- `agents/controller.md`
- references under `skills/implement-v3/references/`
- `.harness-dev/test-compact-returns.py`
- `.harness-dev/test-milestone-complexity.py`

**Changes**

- Run `implement-v3` in a forked Sonnet controller context where supported.
- Keep the invokable skill body to routing, state recovery, invariants, and STOP
  rules. Move detailed review, finalization, and recovery procedures to references
  loaded only for the relevant phase.
- Start each milestone phase from structured state and compact prior artifacts;
  never recover by rereading entire child transcripts.
- Bound controller turns to 20 and set an explicit budget where the runtime
  supports one. Hitting either limit returns a resumable state, not an improvised
  extension.
- Preserve the one-milestone-per-invocation behaviour.

**Acceptance**

- Parent/skill traffic is at most 15% of measured treatment traffic.
- No controller/orchestrator context exceeds 160k tokens in the live fixture.
- A resumed invocation reaches the same state decision using only canonical state
  and referenced artifacts.

### S2.5 — Represent long external jobs without keeping an agent alive

**Files**

- `scripts/check-state.py`
- `scripts/transition-state.py`
- `agents/controller.md`
- `agents/orchestrator.md`
- new `agents/references/external-jobs.md`
- state tests and fixtures

**Changes**

- Add a structured `external_jobs` record while leaving the milestone itself
  `IN_PROGRESS`. Record command class, owner, start time, safe result path, and
  status (`RUNNING`, `COMPLETE`, or `FAILED`). Never store credentials or raw
  commands containing secrets.
- Once a long job is launched, return `WAITING_EXTERNAL` and stop the invocation.
- On the next user-initiated invocation, inspect the result once. Never sleep or
  poll in the foreground.
- Only explicitly approved job classes may use this path.

**Acceptance**

- A fixture can launch, stop, and resume a long job without any foreground wait
  loop or duplicate launch.

**PR 2 exit gate**

- All zero-cost tests and plugin validation pass.
- Static runtime preflight passes.
- After explicit approval, live hook and foreground probes pass on the supported
  runtime.
- The original `implement` skill is unchanged as the A/B control except for
  shared correctness fixes from PR 1.

---

## 7. PR 3 — Economical, risk-aware model and effort routing

**Goal:** Stop paying Opus rates for evidence collection while preserving Opus for
high-consequence judgment where deterministic validation is unavailable.

### S3.1 — Split no-oracle work by risk

**Files**

- `agents/orchestrator.md`
- `agents/controller.md`
- new `agents/references/runtime-contract.md`
- `.harness-dev/test-model-routing.py`
- `.harness-dev/test-milestone-complexity.py`

**Routing taxonomy**

| Reason code | Model/effort | Intended use |
|---|---|---|
| `MECHANICAL_WITH_ORACLE` | Sonnet, low | Narrow edit with deterministic tests |
| `STANDARD_IMPLEMENTATION` | Sonnet, medium | Ordinary implementation/reviewable coding |
| `EVIDENCE_SYNTHESIS` | Sonnet, medium | Logs, repository evidence, compatibility summaries |
| `JUDGMENT_NO_ORACLE` | Opus, high | Security, ambiguous semantics, architecture-critical judgment |
| `ESCALATED_AFTER_FAILED_ORACLE` | Opus, high | Repeated failure where simpler validation is exhausted |

**Changes**

- Replace the broad `NO_TEST_ORACLE => Opus` rule with the taxonomy above.
- Require every Opus dispatch to carry a reason code and a one-sentence risk
  justification in telemetry.
- Evidence synthesis must not silently become architecture decision-making; any
  such decision is a separate `JUDGMENT_NO_ORACLE` task.
- Preserve independent reviewer model selection and avoid downgrading security or
  architecture-critical review solely to meet a cost target.

**Acceptance**

- Former low-risk no-oracle fixtures route to Sonnet.
- High-risk semantic/security fixtures still route to Opus.
- Unknown reason codes fail closed rather than defaulting to Opus or Sonnet.

### S3.2 — Pin effort explicitly

**Files**

- agent frontmatter for controller, navigator, verifier, as-built, worker, and
  reviewer roles
- `agents/references/runtime-contract.md`
- `.harness-dev/test-model-routing.py`

**Defaults**

- Navigator, verifier, and as-built: low effort.
- Mechanical worker: low effort.
- Standard worker/controller: medium effort.
- Independent reviewer: medium by default; high only for named risk classes.
- Opus judgment/escalation: high effort.

**Changes**

- Make model and effort observable in each compact return and telemetry record.
- Reject unsupported implicit combinations in the routing tests.
- Do not change model and effort in the same evaluation comparison unless the arm
  is explicitly labelled as a combined treatment.

**Acceptance**

- Every dispatch fixture resolves to one deterministic model/effort pair and
  reason code.

### S3.3 — Add routing economics to the report

**Files**

- `.harness-dev/measure-context.py`
- `.harness-dev/check-efficiency.py`
- `.harness-dev/test-measure-context.py`

**Changes**

- Report tokens, cost, acceptance, and retry rate by role, model, effort, and
  reason code.
- Flag Opus work with no valid reason code.
- Treat savings from omitted required roles as invalid rather than efficient.

**PR 3 exit gate**

- All zero-cost tests pass.
- Routing fixture accuracy is unchanged.
- No paid run is required for merge; behavioural cost claims wait for PR 4.

---

## 8. PR 4 — Behavioural evaluation, release gate, and promotion

**Goal:** Prove the combined v3 path is cheaper and at least as accurate before it
replaces the current implementation path.

### S4.1 — Add behavioural eval cases

**Files**

- plugin eval definitions in the supported Claude Code format
- deterministic grader scripts under `.harness-dev/`
- `.harness-dev/runtime-efficiency-v3-runbook.md`

**Required cases**

1. Namespaced P2 state and requirement ownership.
2. Two concurrent foreground workers with compact returns.
3. Reviewer stopped before terminal artifact, then safely retried.
4. Reviewer response interrupted after terminal artifact, without duplicate work.
5. REVIEW state attempting to pre-credit criteria.
6. Parent and subagent polling-hook denial.
7. Low-risk evidence synthesis routing to Sonnet.
8. High-risk no-oracle judgment retaining Opus.
9. Existing accuracy fixtures for substantive implementation and review.
10. Long external job stop/resume without polling or duplicate launch.

Each case needs deterministic structural graders first. Use model graders only for
semantic qualities that cannot be reduced to repository tests, and keep them
blind to control/treatment labels.

### S4.2 — Run a controlled A/B campaign

**Arms**

- **Control:** current `implement` path plus shared PR 1 correctness fixes.
- **Treatment:** opt-in `implement-v3` controller plus PRs 2 and 3.

**Protocol**

- Pin harness commit, target fixture commit, Claude Code version, model aliases,
  effort, permissions, environment, and maximum spend in the run manifest.
- Use fresh isolated sessions.
- Run all zero-cost graders before model calls.
- Run three repetitions per arm per selected fixture unless an early hard accuracy
  failure stops the campaign.
- Randomise or alternate arm order to reduce temporal bias.
- Measure only comparable complete runs; report failures and exclusions rather
  than silently dropping them.
- Require explicit user authorization for each paid batch, including a maximum
  total budget.

### S4.3 — Promotion thresholds

All of these must pass:

**Accuracy and correctness**

- No regression in deterministic accuracy fixtures.
- No false PASS or omitted requirement ownership.
- Every accepted milestone has a valid same-HEAD terminal review artifact.
- Forced reviewer interruption recovers without accepting incomplete output.
- Required role coverage is present in every measured successful run.

**Runtime**

- Zero executed polling violations.
- Zero notification-driven collection/re-entry loops.
- Zero hard-limit violations.
- No controller/orchestrator context above 160k tokens.
- Controller/orchestrator median at or below 22 tool-use turns.
- Parent/skill traffic at or below 15% of treatment traffic.

**Economics**

- Treatment median estimated cost per accepted task is at least 20% below control.
- Treatment median total tokens per accepted task is below control.
- Treatment worst successful run does not exceed control worst successful run by
  more than 10% without a documented accuracy benefit.
- Retry/fix-cycle rate is no worse than control.

If accuracy passes but the 20% cost target does not, retain `implement-v3` as
experimental and analyse the per-role report. Do not weaken accuracy gates or
silently promote it.

### S4.4 — Promote or roll back

**On PASS**

- Move the tested v3 controller path into the canonical `implement` skill.
- Preserve a clearly named compatibility alias for one release if needed.
- Update documentation and version metadata.
- Record the control/treatment manifests and aggregate report, excluding private
  transcripts and credentials.

**On FAIL**

- Keep the current `implement` skill as default.
- Revert only the failing PR/work package, not PR 1's correctness fixes.
- Record the failed gate, evidence, and proposed next experiment.

---

## 9. Implementation order inside each PR

Use this sequence for every work package:

1. Add or update the failing fixture first.
2. Implement the smallest production change that satisfies it.
3. Run the targeted test file.
4. Run the complete zero-cost harness suite.
5. Run `claude plugin validate .`.
6. Review the diff for prompt duplication and accidental model escalation.
7. Commit only that coherent work package.

Suggested commit sequence:

1. `fix(state): support namespaced requirement and milestone ids`
2. `feat(review): add terminal review result validation`
3. `feat(state): add guarded milestone transitions`
4. `fix(telemetry): make efficiency evidence fail closed`
5. `feat(runtime): add supported-runtime and hook preflight`
6. `feat(runtime): add opt-in foreground implement controller`
7. `feat(runtime): add resumable external-job state`
8. `feat(routing): split evidence synthesis from judgment`
9. `feat(routing): pin role effort and report reason codes`
10. `test(eval): add v3 behavioural A/B campaign`
11. `feat(implement): promote validated v3 controller` — only after all gates pass

## 10. Definition of done

- [ ] PR 1 completion/state gates work on simple and namespaced real-world fixtures.
- [ ] Efficiency reports fail closed on absent or non-comparable evidence.
- [ ] Supported runtime and active hooks are proved before implementation starts.
- [ ] Parent and child agents run foreground without `TaskOutput` polling.
- [ ] Long jobs stop and resume through structured state.
- [ ] The controller runs in an isolated, bounded Sonnet context.
- [ ] Opus usage is limited to explicit high-consequence reason codes.
- [ ] All zero-cost tests and plugin validation pass.
- [ ] Paid A/B campaign has explicit authorization and complete provenance.
- [ ] Accuracy gates pass in every treatment run.
- [ ] Median treatment cost per accepted task improves by at least 20%.
- [ ] Canonical `implement` is changed only after treatment promotion passes.
- [ ] Private run data, auth material, and unrelated worktree changes are excluded.

## 11. First implementation action

Create `improvement/runtime-efficiency-v3` from `main`, leave private/untracked
evaluation data untouched, and begin with S1.1. Do not upgrade the CLI or execute
paid model calls during PR 1.
