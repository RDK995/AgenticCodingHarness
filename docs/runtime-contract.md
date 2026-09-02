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
| Tool restriction | `agents/worker.md`, `agents/reviewer.md`, `agents/verifier.md`, `agents/as-built.md` frontmatter |
| Plugin packaging | `.claude-plugin/plugin.json`, the `agents/` + `agents/references/` + `skills/` layout |
| Path resolution | `${CLAUDE_PLUGIN_ROOT}` in agent and skill bodies |
| Invocation | `/harness:*` skills, `harness:*` subagent names |

## Required primitives

A runtime can host the harness if it provides these five things.

**1. Fresh-context subagent invocation.** Start an agent from a given system
prompt plus a text packet, with no memory of the caller's context. Used for
orchestrator → worker, implement → reviewer, and implement → orchestrator per
phase.

**2. Per-role tool restriction.** The reviewer declares no `Write` or `Edit`, so
fixing what it is judging is not a step it can take without deliberately reaching
for another route. A runtime that cannot restrict tools at all downgrades even
that to a request.

Be precise about what this buys. The reviewer does declare `Bash`, because it must
re-run validation itself, and a role with `Bash` can write files. The restriction
removes the *convenient* path and makes the *inconvenient* one visible in the
transcript; it is not an enforced guarantee. This document previously claimed the
restriction meant the reviewer "can only ever report findings" — that was
overstated, and §46 records the correction. The guarantee that actually holds is
the structural one: the reviewer is a fresh context that never sees implementation
rationale.

**3. Real file and shell access.** Read, write, edit, search, and run commands.
The entire design rests on executable evidence: tests are run, not described.
A runtime that cannot execute the test suite cannot produce anything the
completion gate will accept.

**4. Structured text return.** The caller parses the reply against a contract —
the worker's `Summary / Files Changed / Tests Run / Result / Unresolved Issues`,
the reviewer's evidence table and `PASS | CHANGES REQUIRED` verdict.

**5. Per-invocation model override.** The caller can run a subagent at a tier
other than the one its definition pins, for one invocation, without editing the
definition. Used by routing and by the retry ladder — Cheap x2, Mid x1, Top x1
before a task is blocked (§47) — and to run the reviewer at the tier of the work
it is judging.

**Total absence degrades safely.** A runtime with no override runs every task and
every review at its pinned tier: all work at `haiku`, all reviews at `sonnet`. The
ladder loses its rungs and weak implementations block sooner — more expensive, and
worse at hard work, but the reviewer is still stronger than the work it judges, so
the gate still means something.

**Partial or silent support does not.** Two cases:

*Partial* — the runtime honours the override for workers but not the reviewer, or
`model:` in `agents/worker.md` is edited upward while the reviewer stays pinned.
Top-tier work then gets a lower-tier review, and the pairing rule is violated
without anything reporting it.

*Silently ignored* — the runtime accepts a model parameter and no-ops it. The
orchestrator believes it invoked a top-tier reviewer and records
`Review tier: opus` in `milestones.md` while `sonnet` actually ran. **The evidence
then asserts a pairing that never happened**, and every guarantee in this harness
rests on evidence being true.

**The asymmetry is what matters.** A silently ignored override in the *ladder*
fails loudly: the attempt runs weaker, fails, and the task blocks. Nothing false
is recorded. The same failure at the *reviewer* is silent — a weaker model emits a
confident per-criterion `PASS`, the gate opens, and the milestone records a strong
review that did not occur. That is this document's worst failure reached not by
configuring a weak reviewer, but by believing a weak one is strong.

**Verify rather than assume.** Before trusting the pairing on a new runtime,
invoke the reviewer with an override and confirm from the transcript that the
model actually changed. If it cannot be confirmed, pin `agents/reviewer.md` to the
top tier and accept the cost on every review — a known cost is better than an
unverifiable guarantee.

Do not emulate the override by editing `model:` in `agents/worker.md`, which
promotes *every* delegated task permanently and quietly inverts the economics the
routing rule exists to protect.

## Capability tiers

The roles differ sharply in how much model capability they need, and the
difference is not about size of output.

| Role | Tier | Why |
| --- | --- | --- |
| `worker` | **Cheap / Mid / Top** | The tier is chosen per task by risk (§47), with `haiku` as the default and a named reason required to go above it (§49): `sonnet` when the task is not clearly specified, not bounded, not low risk or not easily verified; `opus` for architecture, security, cross-cutting or ambiguous work. Nothing it claims is trusted at any tier: a verifier re-runs the validation in a context that did not write the code, and a fresh reviewer checks the result. Failure degrades gracefully — the ladder assumes workers fail. |
| `orchestrator` | **Highest** | Holds the routing decision, the escalation judgement, and the judgement of evidence. It delegates every task and implements none (§46), and since §48 it delegates the re-running of a task's validation too — what it retains is deciding whether the returned command, exit status and file list actually support the claim. Risky work is routed to a worker at this same tier rather than retained. |
| `verifier` | **Cheap** | Re-runs one task's stated validation and reports the command, exit status, output and changed files. Deliberately not the gate, which is what makes a cheap tier safe here: its output is a command and an exit status rather than a judgement, and a tier-matched reviewer re-runs the validation independently before anything becomes `DONE` (§48). It cannot edit what it checks. |
| `navigator` | **Cheap** | Answers *where things are* — line ranges, commit SHAs, file sizes, one command's exit status — so the orchestrator does not spend its opening turns finding out. Cheap for the same structural reason as the verifier and `as-built`: its contract forbids summarising, so it issues no verdict and there is no judgement for a weak tier to get wrong. A brief that characterises a requirement instead of quoting it is a contract violation, not a stylistic one — it would move risk to a cheap tier invisibly. It writes nothing. |
| `as-built` | **Cheap** | Draws what a milestone actually built and, at the end, lays the union against the agreed architecture (§50). Cheap for the same structural reason as the verifier: it issues no verdict, names no severity and suggests no correction, so there is no judgement for a weak tier to get wrong. Its only write is one file under `.harness/as-built/`; the reviewer grades what it recorded. |
| `reviewer` | **Derived — never below the work** | The thing that verifies everything else. Nothing verifies it except a human. Its tier is not fixed: it runs at no less than the highest tier that produced the work under review (§47), with `sonnet` as the floor and the final holistic review at the top tier. A reviewer weaker than the work it judges emits a confident `PASS` and the gate opens on nothing. |
| `roast-requirements`, `architect`, `scope-mvp` | **High** | Their entire value is asking the question nobody had considered — the capability weaker models lack most. `scope-mvp` sits with them because deciding which single outcome is worth shipping first, and what a product can ship without, is the same judgement applied to scope. |

A weak reviewer does not fail loudly; it emits a confident, well-formatted,
per-criterion evidence table saying `PASS`. The harness then records that as
evidence and the completion gate opens. That is worse than having no harness,
because the output *looks* like verification. This remains the harness's most
dangerous failure mode regardless of which tier the reviewer runs at.

**Current assignment is a recorded human decision, not a derivation.** Through
B16 this document put the reviewer at the top tier and called it the one to
protect. The pins were subsequently inverted by explicit instruction:
`orchestrator` to `opus`, `reviewer` to `sonnet`. The reasoning above is retained
because it states a real risk, and the risk is now carried by independent
re-verification rather than by reviewer capability alone — two verification
passes still stand between a worker's claim and a `DONE`. §48 moved the first of
them out of the orchestrator and into the `verifier`, which changes what that
sentence promises: the pass that runs first is now the *cheap* one, and the
tier-matched pass is the reviewer at the end. Whether that substitution holds is an empirical
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
| Which models the worker's three tiers use | The tier table in `agents/orchestrator.md` §Routing rule | Per-invocation overrides, not extra agent definitions |
| Which tier reviews which work | `skills/implement/SKILL.md` §Invoking the reviewer | Derived from the work; never override the reviewer downwards |
| Which model runs the highest tier | `model:` in `agents/orchestrator.md` frontmatter | Verification, routing, and escalation judgement live here |
| Which model runs the high tier | `model:` in `agents/reviewer.md` frontmatter | Lowering it further trades away the last check before the gate; re-run fixtures 01 and 03 |
| Which model re-runs a task's validation | `model:` in `agents/verifier.md` frontmatter | Cheap on purpose — it is not the gate. Raising it buys little; the reviewer is the check that matters |
| Which model draws the as-built record | `model:` in `agents/as-built.md` frontmatter | Cheap on purpose — it records rather than concludes. Raising it buys a prettier diagram, not a safer one |
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
anything defeats the entire design.

Through §47 this was answered by the orchestrator re-running the validation itself
at the top tier — "it must not run on the weak tier". **§48 moved that re-run to
the `verifier` at the Cheap tier, and this is the one place that trade is not
obviously safe.** The argument for it: the verifier did not write the code and has
no stake in the verdict, its job is mechanical rather than judgemental, and a
tier-matched reviewer re-runs the validation independently before the gate. The
argument against it: fabrication is a question of instruction-following fidelity,
not of task difficulty, and cheap models are where fidelity is thinnest.

That was an empirical question and `fixtures/09-vacuous-pass` now answers part of
it. Two false `PASS` claims, each backed by a genuinely green test command: one
where the command does not exercise an acceptance criterion, one where the claimed
change never landed. The Cheap verifier contradicted both — `NOTHING FOUND`
against the uncovered criterion, `Files Changed` derived rather than echoed, and
`FAIL` in each case — and in `05` it contradicted a real worker's `PASS`
unprompted.

**What that establishes, and what it does not.** It establishes that the Cheap pin
does not rubber-stamp: a passing command is not being read as a verdict. It does
not establish that a Cheap verifier will not *fabricate*, and no fixture tries to
induce otherwise — fabrication rather than laziness was the original worry. A
verifier report that a reviewer's independent re-run later contradicts remains the
signal to raise the pin.

**And on a real project one did report what it had not observed.** Under a sandbox
that refused file writes, `/tmp`, `chmod` and subprocesses, a verifier returned a
partial result for a mutation step it had never performed, and reported three test
failures that did not exist — the suite was green. Both symptoms were
environmental, and neither is evidence about the tier: nothing in `verifier.md`
told it what to do when a check could not run, so an honest report had no shape to
take. That gap is closed — the return contract now carries `Checks Not Run`,
`PASS` requires it to be `NONE`, and a check that could not run is explicitly
never a `FAIL`. Whether a Cheap verifier fabricates *without* that excuse remains
unmeasured, and the pin's justification still rests on the reviewer's independent
re-run rather than on the verifier's fidelity.

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
