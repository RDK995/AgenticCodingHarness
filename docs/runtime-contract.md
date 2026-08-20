# Runtime Contract

What the harness requires from the runtime hosting it, and where a different
runtime or a different model plugs in.

The harness ships as a Claude Code plugin, and that is the only configuration
validated. This document exists so the assumptions are stated rather than
reverse-engineered from the agent definitions.

## What the harness is made of

Almost all of it is runtime-neutral text — the task packet contract, the routing
rule, Red → Green → Refactor, the per-criterion evidence table, the finding
contract, the review/fix cap, the milestone completion gate, the human escalation
contract, and the four templates. None of that names a vendor or a model.

The coupling is small enough to list in full:

| Coupling | Where |
| --- | --- |
| Model pinning | `agents/worker.md` frontmatter — one line |
| Tool restriction | `agents/worker.md`, `agents/reviewer.md` frontmatter |
| Plugin packaging | `.claude-plugin/plugin.json`, the `agents/` + `skills/` layout |
| Path resolution | `${CLAUDE_PLUGIN_ROOT}` in agent and skill bodies |
| Invocation | `/harness:*` skills, `harness:*` subagent names |

## Required primitives

A runtime can host the harness if it provides these five things.

**1. Fresh-context subagent invocation.** Start an agent from a given system
prompt plus a text packet, with no memory of the caller's context. Used for
orchestrator → worker, orchestrator → reviewer, and implement → orchestrator per
milestone.

**2. Per-role tool restriction, enforced structurally.** The reviewer has no
`Write` or `Edit`, so it can only ever report findings and never quietly fix what
it is judging. That is a property of the runtime, not a promise in the prompt. A
runtime that cannot enforce it downgrades a guarantee to a request.

**3. Real file and shell access.** Read, write, edit, search, and run commands.
The entire design rests on executable evidence: tests are run, not described.
A runtime that cannot execute the test suite cannot produce anything the
completion gate will accept.

**4. Structured text return.** The caller parses the reply against a contract —
the worker's `Summary / Files Changed / Tests Run / Result / Unresolved Issues`,
the reviewer's evidence table and `PASS | CHANGES REQUIRED` verdict.

**5. Per-invocation model override.** The caller can run a subagent at a tier
other than the one its definition pins, for one invocation, without editing the
definition. Used only by the worker retry ladder: three attempts at the Cheap
tier, then two at the High tier before the orchestrator takes over.

This is the one primitive with a clean degradation. A runtime without it should
skip the escalated attempts and go straight from the Cheap tier to the
orchestrator — the ladder loses two rungs and gets more expensive, but nothing
becomes unsound. Do not emulate it by editing `model:` in `agents/worker.md`,
which promotes *every* delegated task to the High tier permanently and quietly
inverts the economics the routing rule exists to protect.

## Capability tiers

The roles differ sharply in how much model capability they need, and the
difference is not about size of output.

| Role | Tier | Why |
| --- | --- | --- |
| `worker` | **Cheap** | Bounded, clearly-specified, low-risk tasks. Nothing it claims is trusted: the orchestrator re-verifies independently and a fresh reviewer checks the result. Failure degrades gracefully — the retry ladder already assumes workers fail. |
| `orchestrator` | **Highest** | Holds the routing decision, the independent verification, and the escalation judgement. Unrestricted tools by design, because it keeps the risky work — and it is the only role that re-verifies a worker's claim before evidence is recorded. |
| `reviewer` | **High** | The thing that verifies everything else. Nothing verifies it except a human. |
| `roast-requirements`, `architect` | **High** | Their entire value is asking the question nobody had considered — the capability weaker models lack most. |

A weak reviewer does not fail loudly; it emits a confident, well-formatted,
per-criterion evidence table saying `PASS`. The harness then records that as
evidence and the completion gate opens. That is worse than having no harness,
because the output *looks* like verification. This remains the harness's most
dangerous failure mode regardless of which tier the reviewer runs at.

**Current assignment is a recorded human decision, not a derivation.** Through
B16 this document put the reviewer at the top tier and called it the one to
protect. The pins were subsequently inverted by explicit instruction:
`orchestrator` to `opus`, `reviewer` to `sonnet`. The reasoning above is retained
because it states a real risk, and the risk is now carried by the orchestrator's
independent re-verification rather than by reviewer capability alone — two
verification passes still stand between a worker's claim and a `DONE`, and the
higher-tier one now runs first. Whether that substitution holds is an empirical
question, and `fixtures/01-requirement-violation` and `fixtures/03-drift-undeclared`
are the tests that answer it: they are the two that discriminate whether a model
can hold the `reviewer` role at all. Re-run both after any change to these pins.

**Both were run under the current pins on 2026-08-20 and passed** — 13 / 13
expected outcomes, including fixture 03, where every test is green and both
acceptance criteria genuinely hold, so a confident `PASS` would have been the
failure. `sonnet` caught the undeclared drift, graded it `IMPORTANT` rather than
`BLOCKER` or `OPTIONAL`, and kept both criteria at `PASS`. Evidence is recorded
in the B16 section of `.harness-dev/progress.md`.

## Substitution points

| To change | Edit | Note |
| --- | --- | --- |
| Which model runs the cheap tier | `model:` in `agents/worker.md` frontmatter | See the warning below |
| Which model the worker escalates to | The tier named in `agents/orchestrator.md` §Task-level retry and escalation | A per-invocation override, not a second agent definition |
| Which model runs the highest tier | `model:` in `agents/orchestrator.md` frontmatter | Verification, routing, and escalation judgement live here |
| Which model runs the high tier | `model:` in `agents/reviewer.md` frontmatter | Lowering it further trades away the last check before the gate; re-run fixtures 01 and 03 |
| Which model runs the skills | The session model | `roast-requirements` and `architect` are high tier and are not subagents |
| Tool restrictions per role | `tools:` frontmatter | Loosening the reviewer's set removes a structural guarantee |

Every subagent role names its own tier in frontmatter (B16). Before that, only the
worker did, and the other two inherited the session model — which overpaid for the
orchestrator on an expensive session and, worse, silently downgraded the reviewer
on a cheap one. Inheriting is the failure mode this table exists to prevent: the
tier a role runs at should be a decision recorded in a file, not a side effect of
how the session happened to start.

**Do not delete the `model:` line to "unpin" the worker.** Removing it makes the
worker inherit the session model, silently promoting every delegated task to the
expensive tier. Phase 8 requires the cheaper model and B5 cites that exact line
as its acceptance evidence. Change its value; do not remove it.

## How a substitution fails silently

These are the failures that produce plausible output rather than errors.

**Context leakage.** If a runtime implements "subagents" by appending to one
conversation, the reviewer inherits the implementation rationale it is explicitly
forbidden from seeing. Fresh-context review dies without a single error message —
you still get verdicts, they are just worth nothing.

**Rubber-stamping.** A model optimised to be agreeable will not say `FAIL`. Test
this directly rather than hoping; it is the failure mode with no external symptom.

**Contract drift.** Weaker models paraphrase structured returns instead of
reproducing them. The orchestrator then cannot parse a result and either stalls
or guesses.

**Fabricated evidence.** The gate accepts a criterion only with real test
evidence. A model that writes a plausible `Validation` section without running
anything defeats the entire design. The orchestrator's independent re-verification
exists for exactly this, so it must not run on the weak tier.

## Verifying a substitution

B11 and B13 validated sixteen behaviours against fixtures, each with an
independently verified correct outcome. Those scenarios are recorded in
`.harness-dev/archive/B11.md` and `.harness-dev/archive/B13.md`. The five that
discriminate hardest are retained as runnable fixtures under `fixtures/` (B15);
the rest were scratch directories, so re-running them means re-creating them from
the recorded descriptions.

The retained five:

1. **Requirement violation** — `divide(1, 0)` returning `Infinity` must be caught
   as a `BLOCKER` against the stated requirement (B6).
2. **Evidence gate** — an acceptance criterion whose test is missing must be
   `FAIL`, never inferred from a summary (B6).
3. **Loop cap** — contradictory acceptance criteria must reach `BLOCKED` after
   exactly two review cycles, with an escalation contract, rather than looping or
   special-casing the tests to fake a pass (B11).
4. **Architectural drift** — a silently dissolved component boundary must be
   caught **while all tests pass and every acceptance criterion genuinely
   holds** (B13). Nothing in the test output hints that anything is wrong, which
   is what makes this the sharpest discriminator.
5. **Declared deviation** — the same departure, recorded under `## Deviations`,
   must produce no finding (B13). A model that flags it anyway is pattern-matching
   the diff rather than reading the decision log.
