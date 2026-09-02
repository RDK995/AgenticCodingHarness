# Harness Implementation Progress

## Current

Milestone: B28 — Close the defects the 2026-09-02 measurement found (post-V1)
Task: none outstanding — all 7 implemented and fixture-validated.
Status: REVIEW (7 of 7 tasks done; 6 of 7 acceptance criteria proven).

**Not `DONE`, deliberately.** The completion gate requires evidence for every
acceptance criterion, and criterion 7 — *fix cycle >20 turns returns CONTINUE;
median handoff turn ≤22; <10 foreground sleeps; zero off-harness opus lookups* —
names a measurement on the next real project. No fixture can produce it: fixture
phases do not reach 20 turns, nothing in one is slow enough to tempt a `sleep`,
and none contains a live-proof task. Marking this `DONE` would be checking a box
without evidence, which is the one thing this repository's gate exists to stop —
and it is how B26 was handled for the same reason. **B28 becomes `DONE` when the
next real milestone supplies those four numbers**, not before. Everything else is
complete: five fixture invocations, all passing, recorded below.

Also open: B27 remains at REVIEW — task 6, prove the three criteria the fixture
could not reach. Implementation is complete and fixture-validated for the
recording and comparison path; the architect's diagram, the end-to-end wiring
through `implement`, and the reviewer grading `drift.md` are implemented but
unexercised. It does not block B28.

Also open: B25 task 7 is now substantially discharged — see the 2026-09-02
measurement below: `~/tools/harness` was at `1f15d4d` (every change through the
turn budget and navigation hoist in force) for all 18 phoneToLocalModel
milestones, and the turn budget, `/clear` boundary, navigator re-scope and
verifier re-read rule were all exercised and measured. B26's Cheap-share
criterion still needs its tier count read off that project's `milestones.md`
tier tables (task in B28 below).

**Queued for implementation: B28 → B29 → B30 → B31 → B32**, the improvement plan
from the 2026-09-02 measurement. Their sections are at the bottom of this file
and are written to be implemented by a fresh session from this file plus the
named repository files alone. B27 remains at REVIEW; its three unproven criteria
wait on a real run and do not block B28.

## Out-of-milestone measurement — the phoneToLocalModel project, 18 milestones on the current harness (2026-09-02)

Human-directed. The first measurement of the 2026-08-28 changes (turn budget,
navigation hoist, verifier re-read rule) on real work: `phoneToLocalModel`,
2026-08-28 → 2026-09-02, 27 top-level sessions + 358 subagent transcripts under
`~/.claude/projects/-Users-ryankenny-Projects-phoneToLocalModel/`, every one run
against `~/tools/harness` at `1f15d4d`. All figures deduplicated by
`message.id`; script preserved as `.harness-dev/measure-transcripts.py`
(supersedes `measure-context.py`, which still counts per record). Models seen:
`claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5`; list prices throughout.
Accuracy read independently from the project's `.harness/` state (milestones.md,
all 17 archive files, all 7 review reports, both human-redirect artifacts).

**Total: $610.05 · 18 milestones run · mean $31.2, median ~$23** against the
P1-M11 baseline of $34.75. The mean hides the shape: M3–M9/M5a/M15 ran $13–24,
and the tail — M12 $83.21, M10 $65.87, M11 $62.38, M12a-ii $56.42 — is where the
budget violations, fix cycles, `/clear` drift and the accuracy failures all
concentrate. (The two OpenCodeOpenWeightHarness transcripts touched 31 Aug are
P1-M11 at $39.28 and P1-M10 at $53.30 — the pre-change baseline itself,
confirming its numbers.)

| role | cost | share |
| --- | --- | --- |
| orchestrator (impl $225.34 + fix $52.21) | $277.55 | 45.5% |
| **skill session (the parent)** | **$212.97** | **35%** |
| workers | $57.29 | 9.4% |
| reviewers | $35.22 | 5.8% |
| verifiers | $12.80 | 2.1% |
| navigator (49 invocations) | $1.66 | 0.3% |

Coordination is **80.4%** — worse than the baseline's 76%, and the reason is new:
the skill session itself now runs orchestrator-sized opus contexts (peaks 171k,
up to 98 turns, 810k output tokens — 12x the orchestrators' output).

### The three 2026-08-28 changes, measured

1. **Navigation hoist — took.** Orchestrator locate-shaped calls **61% → 18%**
   (224 of 1,238; heuristic counts all Read/Glob/Grep as locate, so 18% is an
   overestimate). Navigator ran **49 times for $1.66 total** (avg $0.034) against
   the baseline's single $0.05 run. This closes the "only test is the next real
   milestone" caveat in the navigator record below.
2. **Verifier re-reads — took.** **21% → 1.9%** exact repeats (54 of 2,864 calls
   across 98 verifier runs; worst individual 20%).
3. **Turn budget — partial.** 44 orchestrator invocations, median 23.5 turns;
   **29 of 44 exceeded 20**. `CONTINUE` fired 11 times but at median turn 26,
   and all 12 continuations resumed cleanly from `milestones.md` with no lost
   state — the mechanism works, late. **Defect: 0 of 7 fix cycles ever returned
   CONTINUE**, including one at 43 turns / 140k — the budget only binds in the
   implementation-phase framing despite the PR #21 fix giving fix cycles a
   CONTINUE path. Worst single violation: M12b's implementation phase, 58 turns,
   no handoff, $16.50. Peak contexts fell from 146–170k to mostly 90–150k.

`/clear` honoured in 24 of 27 sessions; the three that drifted (M10 into M13
planning, M12a-ii into M12b scoping, M13 running a mid-implement requirements
roast) include two of the most expensive sessions.

### New waste, in dollar order

1. **The skill session** ($212.97, 35%): a dispatcher narrating and planning
   in-context at opus prices. Largest unexamined target → B29.
2. **Marathon workers**: the project's biggest contexts are workers, not
   orchestrators — a live-proof worker hit 183.6k / 130 turns / $5.27 with 22%
   repeated (poll-style) calls. "Live proof" tasks dispatched as open-ended
   debugging → B28.
3. **Sleep-polling regressed**: 69 foreground `sleep` calls (P1-M11: 4),
   including an orchestrator running `sleep 90` to wait for subagents → B28.
4. **Off-harness opus lookups**: an $8.13 `general-purpose` and a $2.29
   `Explore` agent doing navigator work — the navigation rule binds the
   orchestrator but not the skill session → B28.

### Accuracy, from the project's own records

The machinery held: 17 milestones DONE, scoping/widening correct in all six
cycle-2 situations (fix cycles proactively disclosed out-of-finding files, which
is what made the widening rule operable), the two-cycle cap honoured — when the
human found a post-cap defect the system correctly offered deferral over
override — every escalation legitimate, every fix cycle wrote its patch file,
and the final holistic review correctly has not run (milestones remain TODO).
**One true post-PASS escape in 17 milestones.** The signature class — green
tests over a mechanism that does not do what it says — appeared **at least nine
times** and was caught before DONE in all but that one. Every failure that
reached the human went through one of three holes:

1. **Reviewer contamination — the costliest single event.** M12 cycle 1's
   reviewer was told, via the implementation phase's framing relayed by the
   skill session, that the repaint and swallowed-error items were "logged
   follow-ups, not criterion breaches" and should not be raised. It passed an
   app that deadlocked on first use; the human's device attestation produced 3
   BLOCKERs, and the M12 cluster (M12 + M12a-ii + M12b) cost ~$164.
2. **Invocation-vs-effect testing.** M12b's inert profile selector escaped two
   passed reviews because its tests asserted the event *dispatched*, not that
   the selection was *reflected* — the lesson M12 had just recorded, unapplied
   in one place.
3. **Inter-milestone coverage gaps.** DOM wiring fell between M9/M10/M11; M5's
   resume mechanism had **zero production call sites** when M16's recon looked;
   the iOS storage assumption fell between Safari proofs and the installed app.
   Each review was right that the gap was outside its criteria; the human's
   phone was the only end-to-end detector, three times.

Also recorded there and still open: the target project has **2 git commits**
across 17 milestones (repeatedly self-flagged; caused verifier stale-baseline
misattributions and forced the snapshot/patch contraption) → B31; the M12a-ii
verifier-sandbox degradation ("a verifier's report currently cannot be trusted
for mutation evidence or full-suite counts") → B28; a false environmental excuse
(M13's probe read `000` and excused the milestone's strongest clause while the
harness was up returning `401`) → B30.

### What this discharges

- **B25 task 7**: substantially. The turn budget (successor to the 90k ceiling)
  and `/clear` were both in force and are measured above. What task 7 wanted —
  a real milestone under the changes — exists eighteen times over.
- **The navigator re-scope's open caveat**: closed, at two orders of magnitude
  more state than the fixtures.
- **B26 Cheap-share**: not yet — needs the worker tier counts read off
  `~/Projects/phoneToLocalModel/.harness/milestones.md` tier tables (B28 task 6).

### Research context (2026-09-02, summarised; full agent reports not retained)

Two research passes were run alongside the measurement. What matters for the
plan: the harness architecture already matches the 2025–26 consensus (stateful
lead + stateless narrow subagents, fresh sessions over rolling compaction,
file-based structured notes, evidence gates); Anthropic's own engineering posts
put multi-agent overhead at 3–10x tokens, so coordination share is attacked by
making coordination cheaper per token, not by restructuring. Evidence-backed
practices adopted into B28–B32: hidden/holdout verification — a mechanical
"test files unchanged" gate drops test-gaming to near zero (ImpossibleBench,
arXiv 2510.20270); LLM reviewers measurably over-flag correct code and detailed
explain-and-fix prompting makes it worse (arXiv 2603.00539), so blocking
findings need runnable evidence; LLM-generated repo context files measured
**−3% success at +20% cost** (ETH, arXiv 2602.11988), so navigation fixes must
be pointers, not prose. **Knowledge graphs: considered and rejected** at this
repo scale — the measured KG wins (RepoGraph +32.8% SWE-bench, LocAgent) come
from repos where grep fails; against a competent agentic-grep baseline the
resolve gain was marginal (arXiv 2606.22417); Anthropic deleted Claude Code's
own index over staleness; and a KG-over-MCP study measured 10x token savings at
**83% vs 92% accuracy** — direct support for the navigator's never-summarise
contract. Revisit only for 10k+-file targets. LSP tools (Serena-class) measured
4x more expensive on simple lookups; reconsider only if telemetry shows
multi-file-refactor queries dominating.

## Out-of-milestone change — splitting the orchestrator by phase (2026-08-25)

Human-directed, outside B27, and prompted by a fair question: the orchestrator
had grown to 912 lines and that felt like too much context. It was, but not for
the reason it looked like.

**What it cost, measured.** `agents/orchestrator.md` was 46.9k chars ≈ **11.7k
tokens**, loaded whole on every phase. On a real fix cycle its first turn was
27,286 tokens, so **43% of its opening context was its own definition** before it
read anything, and across 47 turns its definition was 551k tokens — 10.8% of that
invocation's $7.64. Against B25's finding that the orchestrator is 87% growth and
13% fixed, that puts prompt size at roughly 5% of project cost.

**What is actually phase-specific.** An early estimate of 46% was wrong — it
counted the routing rule, task packets and the implementation loop as
implementation-only, when a fix cycle routes corrections through all three. The
real split: **18% implementation-only, 13% fix-only, 69% shared.**

**Change made.** Two reference files under `agents/references/`, read on dispatch
and named in the dispatch table:

- `planning.md` — reconnaissance, generating milestones, the size/shape check and
  splitting. Read on an implementation phase only; the generation half fires once
  per project.
- `fix-cycle.md` — the fix cycle, the snapshot mechanics, what to record.

Plus a pass removing measurement prose from the core — the 62%-of-cost line, the
35-of-47-shell-commands count, the 110,899-character packet figure, the tier cost
table, the 28k→187k tail. Each kept its rule and dropped its arithmetic. The
evidence lives here, where it can be argued with.

| | before | after |
| --- | --- | --- |
| core, always loaded | 912L / ~11.7k tok | **614L / ~8.0k tok** (−31%) |
| implementation phase | 11.7k | 10.3k (−12%) |
| fix cycle | 11.7k | 9.6k (−18%) |

**Measured on the same fixture, before and after, and the cost result is a wash:**

```
before   orchestrator first turn 27,286   46 turns  2,103,759 read   $7.64
after    orchestrator first turn 22,769   47 turns  2,048,691 read   $7.79
```

Opening context is genuinely **17% smaller** and total traffic 2.6% lower, but
cost moved +2% — inside single-run variance. That is exactly what the structure
predicted: shrinking a prompt that is 13% of an invocation by 31% touches ~4% of
its cost, which noise swamps. **Peak context rose slightly** (61,989 → 64,090),
because a reference read is still a read: the split saves only on the half a
phase does *not* load.

**So this is not a cost change, and should not be recorded as one.** What it buys
is real but different:

- **Consistency.** Five defects were found in the review-layer work above, and
  three were contradictions *between sections* of a document too long to hold in
  one view — the completion gate against the scoped review, the cap check against
  the reviewer invocation that moved in front of it, the final-review dispatch the
  new table removed. Two survived two live fixture runs and were caught only by
  automated review. A 614-line core is the lever on that; the token count was
  never the problem.
- **Phase budget.** The 90k mid-phase ceiling exists to force `CONTINUE` handoffs.
  Opening at 22.8k instead of 27.3k leaves ~5% more of the budget for work.

**Validation.** Both fixtures rebuilt and re-run on the split. `11` widens for the
stated reason, catches the `BLOCKER`, ends `DONE` at `Review Cycles: 2` with three
criteria ticked and its own `M1-cycle2.patch` written. `12` scopes to the cycle-1
patch, one reviewer, no orchestrator, `Review Cycles: 1`. No cross-reference was
left dangling: the skill's pointer to "Snapshot the tree" now names
`references/fix-cycle.md`, and `docs/runtime-contract.md` records
`agents/references/` in the packaging row.

**A defect in the split, caught by `fixtures/05` (2026-08-27).** `11` and `12`
both start at `REVIEW`, so every run of them dispatches to `fix-cycle.md` — the
implementation branch, and therefore `planning.md`, was never exercised. `05` is
the only fixture that starts from nothing, and on its first run **the
implementation-phase orchestrator did not read `planning.md` at all.** It still
reported a size/shape check, performed from the phase summary in the core file,
and reached the right answer on a two-criterion milestone by luck rather than by
rule. Compliance was 1 of 2 orchestrators.

Two changes, and the second is the one that matters:

- **The size/shape check moved back into `orchestrator.md`.** It fires on *every*
  implementation phase while milestone generation fires once per project, and a
  rule that must always run cannot live behind a read that might not happen. This
  costs tokens back — core is 689 lines / ~9.0k tokens rather than 614 / ~8.0k —
  and it is the right trade for the same reason the whole split is: correctness,
  not cost. `planning.md` now holds reconnaissance and generation only.
- **The reference read became the first step of the phase**, in the phase summary
  rather than only in the dispatch table.

Re-run after both: **2 of 2 orchestrators read `planning.md`**, and no agent read
`fix-cycle.md` — the phase that does not need it did not load it, which is the
split doing its job.

**And the final holistic review ran for the first time.** Reaching it takes two
invocations, because the LOOP stops at the milestone boundary. It behaved exactly
as the PR #18 change specified, and recorded so itself:

> Scoped to what no milestone review could see: requirement coverage across the
> whole project, integration as a caller would exercise it, and the
> Constraints/Non-Goals sections. It was **not** handed the project diff — M1's
> diff already carries a fresh Mid-tier cycle-1 PASS.

Top tier, verdict `PASS`, recorded under the `## Final Review` heading PR #18
introduced, with a per-obligation table covering both acceptance criteria, both
functional requirements, the edge case, the constraint and the non-goal. It
re-ran the suite itself and then re-ran it under `python3 -I` from a clean temp
directory — which is what turns "standard library only" from an inference into an
observation. That was not asked for.

`fixtures/05`'s own `EXPECTED.md` needed updating rather than the harness: its
"final holistic review reports COMPLETE" line now records the scoping and the
two-invocation shape, and a new failure mode — *skipping `planning.md` while still
producing a plausible size/shape check* — is written down, since that is exactly
what the first run did and it is invisible in the report.

## Out-of-milestone review — P1-M11, and three changes from it (2026-08-28)

Human-directed. P1-M11 on `OpenCodeOpenWeightHarness` ran 2026-08-28 06:36-08:18
against the **current** harness — every change through `ce0a353` shipped 14 hours
earlier — so what follows is a review of the harness as it now stands, not of a
stale one. All figures deduplicated by `message.id`.

**P1-M11 cost $34.75** across 17 subagent contexts:

| | cost | share |
| --- | --- | --- |
| orchestrator — implementation phase | $14.38 | 41% |
| orchestrator — fix cycle | $6.67 | 19% |
| skill session | $5.21 | 15% |
| **coordination subtotal** | **$26.26** | **76%** |
| workers (5) | $3.80 | 11% |
| verifiers (7) | $2.43 | 7% |
| reviewers (2) | $2.21 | 6% |
| navigator (1) | $0.05 | 0.1% |

### What the review-layer work bought, measured on a real milestone

The PR #17-#19 chain validated itself in the field, first time out. Cycle 1
recorded `Pre-correction: ebc4d02…`; the fix cycle recorded that its corrections
touched two files no finding named; **cycle 2 widened back to the whole milestone
for exactly that reason**, naming `harness/api/server.test.ts` and
`docs/api/…v1.md` against a finding that named only `harness/api/server.ts`.
Verdict PASS on five criteria. `Review Cycles: 1` — the corrected counting is
honoured. The snapshot mechanism ran (9 `git commit-tree` calls) and the reviewer
confirmed a file byte-identical across the pre-correction snapshot, the
post-correction snapshot and the working tree.

And it is cheap: **two review cycles for $2.21**, against P1-M10's three cycles at
$18.42 in the same window.

Other practices clean: zero `.output` reads (was 52 of 58 `Read`s historically),
zero orchestrator edits to source, packets and reports by path throughout, tier
mix 11 `haiku` / 4 `sonnet` / 4 `opus`, 4 sleep-polls (was 23), `/clear` honoured
between M10 and M11.

### Three deviations, and the changes made

**1. The context ceiling fires at ~1.6x its stated threshold — $13.46 of $34.75
(39%).** `CONTINUE` *is* returned (M10 shows a continuation and a resumption), but
M10's implementation phase ran to 169,736 tokens first and M11's to 145,929
without handing off at all. The cause is structural and is the same one M5a found
for `/clear`: **an agent cannot observe its own context size**, so "past roughly
90k tokens" is a condition it can only guess at.

Changed to a count it can keep. Across **63 measured orchestrator invocations**,
context crossed 90k at a median of **turn 19** (min 10, max 40), so the rule is
now *"count your turns; at 20, stop taking on new work and hand off"*, with 90k
retained as the stated reason and the proxy's limits spelled out. The skill's
continuation cap went 3 → 4 to match: shorter phases mean more continuations, and
5 phases x 20 turns is comparable to what phases were actually consuming — of
those 63 invocations only 2 ran longer, and both were oversized milestones the cap
exists to surface.

**2. Navigation is 61% of the orchestrator's tool calls; the navigator ran once,
for $0.05.** 39 of 64 tool calls were locate-shaped, worth about **$13.91** at the
blended $0.357 per orchestrator call. The re-scope shipped the previous evening
did not take. Best explanation: it was a `###` subsection under a heading about
the state file's size, so it read as opening-pass advice however its body was
worded. Promoted to a top-level rule sitting **beside the routing rule**, ending
with the diagnosis — *routing decides who does a task; this decides who does a
lookup; they are the same question*. The seam it left is fixed: the file-size
section told the orchestrator to run `wc -l` itself, which the rule now forbids,
so it takes the count from the navigator's opening brief.

**3. Verifier re-reads.** `Verify P1-M11-T2` made 7 exact repeat calls of 33
(21%). `worker.md` has had a never-read-twice rule since M4b; `verifier.md` never
got one, flagged as a follow-up in the M5a analysis and open since. Added, worded
so it cannot be read as "check less": *re-running a command is not a re-read; if
you need to see a test run twice, run it twice and report both.*

### Validation, and what it cannot show

`05` and `11` re-run, both pass. `05` reached `DONE` with three criteria and a
green suite; `11` widened for the recorded reason, caught the `BLOCKER`, ended at
`Review Cycles: 2` with both patches written. Nothing regressed.

**But the fixtures cannot test change 2 at all.** They generate 7-12% navigation
against the real project's 61%, because there is almost nothing in them to
navigate: 12 tracked files against 405. Before and after the hoist the fixture
numbers are 7% / 3 navigator calls and 12% / 2 — noise at that size. **The only
test of change 2 is the next real milestone**, and the same is true of change 1:
no correctly-timed handoff has ever been observed, so its ~20% saving is a model,
not a measurement.

Expected if both hold: roughly $35 → $20 per milestone. Change 3 is worth about
$0.30 and is certain.

### A defect in change 1, from automated review of PR #21

The turn budget was written into `## Context boundaries`, which is
**phase-agnostic**, so it told every phase to return `CONTINUE` — while the skill
handled `CONTINUE` only inside the `TODO`/`IN_PROGRESS` branch. Two real failures,
plus a third the review did not name:

- **A fix cycle at 20 turns.** `references/fix-cycle.md` said it must return
  `REVIEW` or `BLOCKED`. Returning `REVIEW` mid-corrections sends half-corrected
  work to a reviewer and spends a cycle of the two-cycle cap on it; returning it
  *without* incrementing `### Review Cycles` trips the skill's "the cap is not
  being honoured" stop and reports a harness defect that is not one.
- **Generation at 20 turns.** No continuation path exists at all, so a partial
  `milestones.md` would be read by the LOOP as the project's plan.
- **The final-review fix cycle**, which reads the same reference and therefore
  inherited the ability to return `CONTINUE` with nothing handling it.

Fixed per phase rather than by restricting the budget to implementation, because
two of the three genuinely need to continue:

```
implementation phase  →  CONTINUE, as before
fix cycle             →  CONTINUE, and must NOT increment Review Cycles —
                         the cycle is unfinished, so it has not happened
final-review fix      →  CONTINUE, same treatment
generating milestones →  never. Write the plan in full or write nothing:
                         a half-plan is indistinguishable downstream from a
                         whole one. Return BLOCKED with the recon completed.
```

The skill gained a `CONTINUE` branch for both fix-cycle kinds — fresh
orchestrator, **same report path**, capped at 4, and no reviewer between
continuations — and a `BLOCKED` branch for generation, plus a structural check
that the last milestone is complete before entering the LOOP. Producer/consumer
symmetry now holds for all four paths.

`05` and `11` re-run and pass: `05` `DONE` with a green suite, `11` widened,
`Review Cycles: 2`, both patches written.

## Out-of-milestone change — the navigator, re-scoped (2026-08-27)

Navigation is **54% of the orchestrator's tool calls** on a mature project —
1,658 of 3,062, deduplicated — and it is the one number from the cost analysis
that survived the correction below, because it is a count of tool calls rather
than a sum of usage.

It does not cluster at the opening. It runs at roughly a fifth of tool calls from
the first turn to the last, and **two thirds of it happens after the first 20% of
a phase**. The instruction said "invoke the navigator for that opening pass", so
it missed most of what it was written for — and the navigator ran **10 times
across an entire project** against those 1,658 calls.

Rewritten as a trigger rather than a phase: *before running `wc`, `ls`, `find`,
`sed -n`, `head`, `tail`, `grep`, `git rev-parse`, `git status`, `git log` or
`git branch` to find out where something is, that is a navigator call and not
yours* — with two narrow exceptions, a single command whose answer decides the
next thing said, and anything under `.harness/` small enough that locating it
costs more than reading it. `agents/navigator.md` now expects several invocations
per phase and a batch of unrelated questions in each. Its never-summarise contract
is unchanged, and that is what keeps a Cheap tier safe for the wider scope.

**Validation.** `05` and `11` re-run, both pass, and the change is visible in the
traces: `05` invoked the navigator **twice** where these runs previously invoked
it zero or once — `Locate repo baseline and layout`, then `Run milestone
validation commands` mid-phase — and `11`'s fix cycle opened with `Locate repo
state for M1 fix cycle`. `05` reached `DONE` with its suite green; `11` widened,
caught the `BLOCKER`, and ended at `Review Cycles: 2` with three criteria ticked
and both its patches written.

**What that evidence cannot show, with the sizes stated rather than gestured at.**
`11` starts from **12 tracked files** — 85 lines of Python across five modules and
three test files — and a 93-line seeded `milestones.md`. `05` starts from **one
file**, its 35-line `requirements.md`. Against them, the project the 54% came from
carries **405 tracked files**, a 2,429-line `milestones.md`, and 18,978 further
lines under `.harness/archive/`.

So there is very little in a fixture to navigate *to*, and two navigator calls is
near the ceiling of what one can demonstrate. Whether the trigger holds at two
orders of magnitude more state is the measurement that matters, and it has not
been taken. It is the same measurement that would settle whether navigation is
still a real target at all: the fixtures put it at 9% of tool calls and the real
project at 54%, and the difference between those is project size, not definitions.

(An earlier draft of this paragraph called these "4-file fixtures" and cited a
"3,800-line `milestones.md`". Both were wrong — four is the number of files `11`'s
seeded *correction* touches, not the fixture's size, and the state file has since
been archived down to 2,429 lines. Corrected after review, and recorded rather
than quietly edited, because the paragraph uses those sizes as its evidence.)

**Not done: a companion "batch your tool calls" rule.** Its premise — 1.00 tools
per turn, never batches — was the artefact corrected below. The agents already
batch.

## CORRECTION — every cost figure below is inflated ~1.70x (2026-08-27)

**The measurement method was wrong.** Claude Code's transcripts split one API
response across several `assistant` records that share a `message.id`: the text
block is one record, each tool call is another, and **every record carries the
same `usage` object**. Summing over records therefore counts one response two or
three times. All the cost analysis in the sections below summed over records.

Verified on the largest subagent transcript: 148 records, 93 distinct
`message.id`s, 26.4M tokens summed over records against 16.4M deduplicated —
**1.61x** in that file, **1.70x** across the project.

```
                              as reported      deduplicated
project total                     $3,474            $2,042
orchestrator                      $1,594  (46%)       $923  (45%)
reviewer                            $410  (12%)       $263  (13%)
verifier                             $70                $35
```

### What was wrong, and what still holds

**Wrong, and one of them backwards:**

- *"Coordinating review ($494) costs more than reviewing ($410)."* **False, and
  reversed.** Deduplicated it is **$183 against $263 — reviewing costs more.**
  This was the headline of the review-layer analysis and of PR #17.
- *"53% of orchestrator turns issue no tool at all."* Actually **7%**. The 53% was
  text blocks of tool-calling responses counted as separate no-tool turns.
- *"1.00 tools per tool-turn — it never batches."* It does batch: 1.08 tools per
  API call for the orchestrator, 1.75 for `Explore`. **Zero** multi-tool records
  across 21,281 tool-calling records machine-wide should have been the tell — that
  is not a behaviour, it is a format.
- Every per-turn and per-invocation figure: the $0.388/turn, the $7.64 fixture
  orchestrator, the before/after split comparison ($7.64 → $7.79).

**Still holds:**

- The review layer is **~22%** of project cost, against 26% as reported. Same
  order; the conclusion that review is a large minority of spend stands.
- Role shares barely move — orchestrator 46% → 45%, reviewer 12% → 13%.
- **Six review cycles instantiated a coordinator that had nothing to route.** A
  count, not a cost, and unaffected.
- Navigation is **54% of the orchestrator's 3,062 tool calls** (1,658), on a
  deduplicated basis.
- Everything about *what reviews caught* — the `os._exit(0)` grader, the
  "documents more than it enforces" class, the per-cycle finding tables. Those are
  finding counts read from `.harness/archive/`, not from transcripts.
- Every fixture result in this file. All of them are behavioural.

### Does anything need reverting?

No. The four review-layer changes were validated behaviourally by fixtures `11`,
`12` and `05`, not by the cost argument, and the waste they remove is real if
smaller than claimed. What was overstated is the *motivation*: PR #17 justified
moving reviewer invocation into the skill partly on an asymmetry that does not
exist. The change still stands on the six no-op coordinator instantiations and on
the fixture evidence.

**The shipped files carry none of this.** The B12 pass above had already removed
every dollar figure from `agents/` and `skills/`, for unrelated reasons. The
inflated numbers survive only in this file, in the PR descriptions for #17-#19,
and in commit messages.

**Method note for anyone measuring this again:** deduplicate by
`message.id` before summing `usage`, and count API calls rather than `assistant`
records. `.harness-dev/measure-context.py` predates this correction and counts
per record — it needs the same fix before it is trusted again.

## Out-of-milestone change — the B12 deletion pass, and a dispatch gap (2026-08-27)

B12's question applied to the shipped set: what can be deleted while preserving
the required behaviour?

**Cross-file duplication is already low.** A shingle comparison across
`orchestrator.md`, both references, `implement/SKILL.md`, the milestones template,
`worker.md`, `verifier.md`, `reviewer.md` and `runtime-contract.md` found exactly
**two** overlapping passages. So the pass is within-file: rationale, measurement
narrative, and rules restated near where they were already stated.

**Deleted, with what each removal costs in behaviour:**

- The archiving exceptions in `orchestrator.md`, restated from the template it
  points at in the same breath. Collapsed to one line rather than deleted, because
  fixture `05` showed a pointer can be skipped and these three are the safety
  rules.
- Three paragraphs of verifier *design rationale* — why the role is pinned Cheap,
  why its `tools:` omit `Write`. `docs/runtime-contract.md`'s tier table owns that.
  The orchestrator needs to invoke the verifier and judge its return, not to know
  why the tier is safe.
- The remaining measurement citations Context boundaries kept through the last
  pass — "52 of 58 `Read` calls", "23 of them".
- The phase-return paragraph, which restated "Which invocation this is" from the
  same file.
- The second half of "Read in ranges", which restated the first.
- Two paragraphs of hand-off rationale for a one-line rule.
- The runtime-cannot-override fallback — `runtime-contract.md` §"Total absence
  degrades safely" owns it.
- In `implement/SKILL.md`, three separate measurement narratives supporting the
  same rule (one session per milestone). Collapsed to one, keeping the M5a case,
  because that is the one explaining why the rule is a *gate on the way in* rather
  than an exit instruction — the form it already failed in once.

`orchestrator.md` −2,500 chars from deletion, `implement/SKILL.md` −695,
`worker.md` −132.

**A dispatch gap, from automated review of PR #19.** The dispatch table keyed every
case on milestone `Status`, and the preamble said status is the authority and to
*stop rather than guess*. On a greenfield project there is no status, so the
skill's "invoke the orchestrator to generate milestones" matched no case, and the
safest reading of the rule pointed at stopping. `fixtures/05` had papered over it:
the model inferred an implementation phase and read `planning.md` anyway. Fixed
with an explicit first row and a phase description naming what `planning.md`
carries that generation cannot do without.

**Validation.** All three fixtures re-run after the pass. `05` — both
orchestrators read `planning.md`, including the generation one under the new
dispatch case, `DONE`. `11` — widens, `BLOCKER`, `Review Cycles: 2`, its own
`M1-cycle2.patch`. `12` — scoped to the cycle-1 patch, one reviewer, no
orchestrator, `Review Cycles: 1`.

## Out-of-milestone measurement — what the review layer costs and catches (2026-08-25)

Human-directed, outside B27. Recorded here because it changes four shipped
definitions and because it is the first measurement of the *review* layer rather
than the coordinating one.

**Where the measurement came from.** The whole of `OpenCodeOpenWeightHarness` —
7 milestones, 18 review cycles, 7 sessions and 276 subagent contexts — read from
the Claude Code transcripts under
`~/.claude/projects/-Users-ryankenny-Projects-OpenCodeOpenWeightHarness/`, costed
per model tier at list price, and cross-read against every `### Review` section in
that project's `.harness/archive/M*.md`. Cycle attribution comes from subagent
descriptions, so the cycle-1/cycle-2 split of the *reviewer's* own cost is
approximate — 10 of 18 reviewer invocations carry no cycle number. The layer
totals and the per-milestone findings are exact.

### What review costs

| Layer | n | Turns | Cost | Share |
| --- | --- | --- | --- | --- |
| orchestrator — implementation phases | 18 | 2,394 | $1,100 | 31.7% |
| orchestrator — review/fix cycles | 18 | 1,485 | **$494** | **14.2%** |
| reviewer subagent | 18 | 1,667 | **$410** | **11.8%** |
| worker (of which ~$204 was correction tasks) | 120 | 10,902 | $908 | 26.1% |
| verifier | 92 | 7,191 | $70 | 2.0% |
| navigator | 5 | 315 | $2 | 0.1% |
| **project total** | | | **$3,474** | |

**Review is 26% of the project, ~32% with the fix work it generates.** The line
that decided the changes below: **coordinating review ($494) costs more than
reviewing ($410)**, because every cycle instantiates a fresh orchestrator to route
findings — including the six cycles that returned `PASS` with nothing to route.

### What review catches

~9 `BLOCKER` and ~26 `IMPORTANT` findings across 18 reviews, about $32 each. The
question is whether anything cheaper would have caught them, and on the sample
it would not:

- **M4a** — the reviewer drove a real agent through the real sandbox and found
  that an agent which changed nothing, added one file containing `os._exit(0)`,
  and *narrated* a fix was graded `PASS` on 12 of 16 fixtures. `gate:evals`
  reported PASS on a corpus defeated 16/16.
- **M3** — 1 `BLOCKER` and 4 `IMPORTANT`, every one of the form *documents more
  than it enforces*: a vacuity guard that did not exist while the gate printed
  11/11 proven; a gate claiming to read the kernel's socket table that read what
  unprivileged `lsof` reports, blind to 3 of 6 listeners. That phrase recurs
  through the project — the findings label themselves the sixth and seventh
  instance.
- **M5b** — tool-name mis-attribution resolving to a *wrong* name rather than
  throwing, active during the AC10 evidence run.
- **M4b** — a guard test that asserted nothing.

One class, and it is the class the harness exists for: **green tests, genuinely
satisfied acceptance criteria, and a mechanism that does not do what it says.**
The verifier structurally cannot catch it — it re-runs the stated validation,
which passes. The tests cannot — they are the thing being defeated. This is the
`fixtures/03` scenario occurring repeatedly in the field.

### Where it is not earning

**Cycle 2.** Seven second cycles, $265:

| Milestone | Cycle 2 outcome |
| --- | --- |
| M2 | `PASS` — 0 BLOCKER, 0 IMPORTANT, 9 OPTIONAL |
| M4c-i | `PASS` — 0 BLOCKER, 0 IMPORTANT, 3 OPTIONAL |
| M4a | 1 BLOCKER, 3 IMPORTANT — real (the `os._exit` exploit) |
| M1 | 2 new IMPORTANT — real |
| M4b | CHANGES REQUIRED at the cap → escalation → resolved by human direction |
| M5b | 1 IMPORTANT, 6 OPTIONAL at the cap → BLOCKED → discharged by a human scope ruling |

Two of seven paid. Two returned clean at full price. Two produced findings a human
had to *rule on* rather than fix, surfaced at the cap, which is the most expensive
place to surface a scope dispute. Note also which milestones cycle 2 paid on: M4a
carried 12 acceptance criteria, and under the 3-5 budget that milestone would not
exist in that form.

Against that, the sharpest number in the set: **"Fresh review of M4b correction" —
51 turns, $1.98 — found a real `BLOCKER`.** A review scoped to the correction diff
cost a tenth of a full cycle 2 ($14-55 each) and out-yielded most of them.

**The final holistic review has never run.** Not once, across 7 milestones. The
project has never reached all-DONE, so `implement`'s final review — specified at
the top tier over the entire project diff — has no evidence behind it at all.

### Changes made

1. `skills/implement/SKILL.md`, `agents/orchestrator.md` — **the skill invokes the
   reviewer, not the orchestrator.** On `PASS` the skill applies the completion
   gate itself and sets `DONE`; the orchestrator is invoked only when there are
   findings to route, and can no longer return `DONE`. The gate is mechanical —
   count the reviewer's per-criterion rows against the milestone's criteria,
   confirm no BLOCKER or IMPORTANT remains — so no verification depth is given up;
   what goes away is six no-op coordinator instantiations. Reviewer tier
   derivation moved to the skill with it, and `docs/runtime-contract.md`'s
   substitution table now points there.
2. `skills/implement/SKILL.md`, `agents/reviewer.md`, `agents/orchestrator.md` —
   **a second review is scoped to the correction diff**, plus the criteria those
   corrections touch, and widens back to the whole milestone if a correction
   changed a file no cycle-1 finding named. The fix cycle is now required to
   record the correction's changed files under `### Review`, and to call out any
   file outside the findings — that record is what the scope rests on.
3. `skills/implement/SKILL.md`, `agents/reviewer.md` — **the final review no
   longer reads the whole project diff.** It is scoped to what no milestone review
   could see: requirement coverage across milestones, integration between them,
   and drift from `drift.md`, with the validation it re-runs itself. Every
   milestone diff already carries a fresh reviewer's verdict at the tier that
   produced it. The full-diff form is retained as a deliberate human request — a
   release gate, a handover, an audit — and the section states outright that this
   review has never been exercised.
4. `skills/implement/references/milestones-template.md`, `README.md` — new
   `.harness/reviews/` scratch directory. A `CHANGES REQUIRED` report is written
   there once and passed to the fix cycle by **path**, not re-emitted into a
   prompt. Same defect and same fix as task packets before M4b; findings reports
   are the larger documents.

5. `fixtures/11-correction-wandered`, `fixtures/12-scoped-second-review` — a
   paired fixture for changes 1 and 2, built on a four-file `receipt` project.
   In `11` the cycle-1 correction is correct, fixes its finding, leaves the suite
   green — and edits `receipt/total.py`, which no finding named, changing amounts
   from dollars to cents while `receipt/report.py` still formats them with
   `"$%.2f"`. `python3 -m receipt receipt.txt` prints `$1999.00 … TOTAL $2506.00`
   against a criterion naming `$19.99 … TOTAL $25.06`, and `### Validation` holds
   a *correct* CLI transcript from before the correction, so a review that credits
   the record misses it. In `12` the correction stays inside its finding and the
   repository is genuinely correct: the second review must stay scoped, and the
   `PASS` must complete the milestone with **no orchestrator invoked** — the only
   test of change 1 that exists. Neither runs alone: `11` by itself rewards
   widening every time, which is the behaviour the measurement priced.
   Both were checked to behave as their `EXPECTED.md` states — `11` is 4 tests
   green with a broken entry point, `12` is 6 tests green with a correct one.

**A defect in change 1, found by writing the fixtures.** Moving reviewer
invocation to the skill moved it *in front of* the two-cycle cap, which the
orchestrator checked. The skill would have invoked a third reviewer before
anything checked the count — silently restoring the unbounded loop the cap
exists to prevent, and breaking `fixtures/08` in the process. Fixed by checking
the cap in the skill, before any reviewer is invoked, and giving the orchestrator
an explicit **escalate** mode: `Status: REVIEW` with the cap spent and no report
path means set `BLOCKED`, write the Human Escalation Contract from what
`milestones.md` records, route nothing. Escalation stays at the top tier because
"what should a human decide" is judgement, not assembly. `fixtures/08`'s command
moved from `--agent harness:orchestrator` to `/harness:implement` with the change
recorded in its `EXPECTED.md`; its expectation is unchanged.

**Both fixtures were run, on 2026-08-25, against this working tree. Both pass,
and between them they found three defects — all three in these changes, none in
the harness they were testing.**

`11` — the discriminating behaviour held exactly. Cycle 2 widened, and said why:
*"widened to the whole milestone, because cycle 1's correction changed
`receipt/total.py` and `tests/test_total.py`, which no cycle-1 finding named"*.
It re-ran `python3 -m receipt` itself rather than crediting the stale transcript
in `### Validation`, graded AC3 **FAIL**, and raised a `BLOCKER` naming
`receipt/report.py` — tying it to the correction's change of representation
rather than blaming the correction. The suite was 4/4 green throughout. The
re-run then showed the *other* half of the rule in the same milestone: the third
review was **scoped**, not widened, "because every file [it touched] was named by
a finding".

`12` — the negative held too, and it is the only isolated test of change 1:

```
harness:reviewer | M1 cycle-2 scoped review      ← and nothing else. No
                                                   orchestrator was invoked at
                                                   all on the passing path.
```

No `.harness/reviews/` file was written; the review recorded that it stayed
scoped and why; and it raised nothing at any severity against correct code. It
also verified the cycle-1 fix falsifiably rather than by reading it — running the
named cases against both the pre-fix and post-fix commits, and confirming the two
added tests fail against the pre-fix implementation.

**The three defects, all in this change set.**

1. *The cap check had moved in front of itself.* Found while writing the
   fixtures, before any run: putting reviewer invocation in the skill put it
   ahead of the cap the orchestrator checked, so a third reviewer would have been
   invoked before anything counted. Fixed by checking the cap in the skill and
   giving the orchestrator an explicit escalate mode.
2. *Passing reviews were incrementing the cycle counter.* Found by `11`'s first
   run, which reported it itself: `Review Cycles` reached `3` on a milestone
   corrected twice, and the guard "STOP if the fix cycle returns REVIEW with
   Review Cycles already at 2" then fires on the normal path, contradicting the
   top-of-loop cap check and making the cap unreachable. Fixed — a cycle is a
   review **whose findings were routed and fixed**; a passing review ends the loop
   and does not increment. `11`'s re-run confirms it: `Review Cycles: 2`, with the
   file noting *"(Not incremented by the passing review.)"*.
3. *`DONE` was being recorded with every acceptance criterion still unchecked.*
   Found by `12`. Moving the completion gate from the orchestrator to the skill
   carried the *checking* across but not the instruction to **check them off** —
   the orchestrator's wording was "verify it yourself against the reviewer's
   per-criterion evidence table before checking it off", and only the first half
   survived the move. `11` happened to tick them and `12` did not, which is what
   an under-specified instruction looks like. The skill's PASS path now ticks each
   box against the reviewer's row and nothing else. `12` was re-run after the fix
   and records `Status: DONE`, `Review Cycles: 1`, all three criteria `[x]`, no
   `.harness/reviews/` file, and one subagent — the scoped reviewer.

`11`'s own `EXPECTED.md` was wrong too, and was corrected rather than the harness:
it asserted `Status` is not `DONE`, written as if the run stops at the cycle-2
verdict. It does not and should not — the loop routes the finding, fixes it, and
re-reviews, and a `DONE` reached that way is correct. Its setup was also rebuilt;
the third commit was `--allow-empty`, so there was no correction diff for a scoped
review to be scoped to.

**Three further defects, from automated review of the PR.** All three were real
and all three are fixed; the first two would have shown up on the first real
milestone that used them, and the fixtures could not have caught either.

1. *A scoped review deadlocked against its own completion gate.* "What a second
   review sees" gave the reviewer "the acceptance criteria those corrections
   touch", while the gate requires a per-criterion row for **every** criterion.
   A correctly scoped review of a one-criterion correction would therefore fail
   the gate with no finding for a fix cycle to route — burning a cycle of the cap
   on a correct milestone. Both live runs had resolved it by grading everything
   anyway, which is exactly how an ambiguous instruction hides. Fixed by saying
   what was always meant: **the reading narrows, the grading does not.**
   Re-grading is nearly free — the reviewer re-runs validation and the entry
   point regardless; re-reading a milestone diff cycle 1 already read is what
   costs.
2. *A list of filenames is not a diff.* The scope was "the files the fix cycle
   recorded", but the harness does not commit after every task, so a milestone's
   implementation and its corrections routinely sit in the working tree together
   — `git diff <baseline> -- <those files>` returns the original implementation
   of them alongside the correction, which is the whole milestone under a
   narrower name. The fixtures hid this because their setup uses three commits.
   Fixed: the fix cycle records `Pre-correction: <sha>` before routing anything,
   via `git stash create`, which snapshots the working tree without touching it;
   the scope is `git diff <sha> -- <files>`. A missing ref means there is no
   correction diff and the review reads the whole milestone.
3. *Final-review corrections had no dispatch path.* The skill still invoked the
   orchestrator with the final reviewer's findings, but every milestone is `DONE`
   by then and the new dispatch table only accepts a fix for a milestone at
   `REVIEW` with a report path — so that invocation matched no phase and would
   have stopped. Fixed with an explicit final-review fix mode: the skill writes
   the report to `.harness/reviews/final-cycle<n>.md`, and the orchestrator
   records the loop under a `## Final Review` heading in `milestones.md` with its
   own 2-cycle count, separate from any milestone's.

Both fixtures were re-run after the amendments and both still pass. `12` states
the fix in one line — *"Scoped to the correction diff (`git diff 779c184 --
receipt/parse.py tests/test_parse.py`), since the correction changed no file
outside the cycle-1 finding. All three criteria were re-graded, not just the
corrected one."* `11` still widens, still catches the `BLOCKER`, still ends at
`Review Cycles: 2` with three criteria ticked.

**Defect 3 is unexercised.** No fixture reaches all-milestones-`DONE`, and the
final review has never run on any project, so its correction path is now
*specified* rather than *tested*. That is the same gap the final review itself
carries, one level down.

**Two more, from automated review of the follow-up PR. Both valid; the first was
understated.**

1. *`git stash create` cannot snapshot untracked work, and the failure is silent
   in two ways.* Verified directly: `git stash create` takes `[<message>]` and
   nothing else, so a `-u` added to "fix" it is swallowed **as the message** and
   the command appears to work — two parents, no untracked capture. And the
   consequence is worse than an omission: even given a snapshot that does contain
   the file, `git diff <snapshot> -- <untracked path>` reports it **deleted**,
   because git's worktree side does not see untracked paths. A scoped review
   would have been handed an actively wrong diff, not merely a short one. This
   matters precisely because the harness permits a milestone to add a file and
   never commit it.

   Replaced with a throwaway-index snapshot taken **twice** — before routing and
   after validating — with the correction diff written between the two:

   ```
   IDX=$(mktemp -u); GIT_INDEX_FILE=$IDX git add -A
   TREE=$(GIT_INDEX_FILE=$IDX git write-tree); rm -f "$IDX"
   git commit-tree "$TREE" -p HEAD -m snapshot
   ```

   Verified to capture tracked and untracked alike, to catch files the correction
   itself creates, to honour `.gitignore`, and to leave index, worktree and stash
   untouched. Snapshot-to-snapshot is load-bearing: snapshot-to-worktree
   reintroduces the deletion artefact. The fix cycle now writes
   `.harness/reviews/<milestone>-cycle<n>.patch`, and **the patch** — not a ref,
   not a file list — is what the next review is scoped to, which also keeps the
   plumbing out of the reviewer's prompt.

2. *`sed -i ''` is BSD-only.* On GNU sed the empty suffix is parsed as the script
   and the `s///` as a filename, so both fixture setups would have exited 2 before
   substituting, leaving the literal placeholder committed and the scoped `git
   diff` reference invalid. Both now use `sed ... > tmp && mv`, checked under GNU
   semantics.

**`11`'s re-run proved the first fix on live work, by accident.** Its cycle-2
correction created two test files, `tests/test_main.py` and `tests/test_report.py`,
and left them **untracked** — `??` in `git status`, absent from `git ls-files`.
The patch the fix cycle wrote contains both:

```
+++ b/receipt/report.py
+++ b/tests/test_main.py
+++ b/tests/test_report.py
```

Under `git stash create` the next review would have been scoped to
`receipt/report.py` alone and never seen the two tests the correction added. The
defect was not hypothetical, and the fixture reproduced it on the first run after
the fix.

Both fixtures pass on this mechanism. `12` records *"Scoped to the correction
patch `.harness/reviews/M1-cycle1.patch`, per the second-review rule: the reading
narrowed to the correction, the grading did not."* `11` widens as before, and its
fix cycle produced its own `Pre-correction` ref and `M1-cycle2.patch`.

**Considered and not done.**

- *Dropping cycle 2 when cycle 1 found no BLOCKER.* This was the initial proposal
  and the evidence does not support it. M2 and M4c-i suggest it, but the M4b
  post-cap review found a real BLOCKER **in a correction** — corrections carry
  their own defects, and a milestone whose corrections are never reviewed has an
  unreviewed diff in it. Scoping cycle 2 gets most of the saving without that
  hole, so the rule became "always run it, scoped" rather than "run it sometimes".
- *Lowering the reviewer tier.* Nothing here argues for it. M5a — a
  properly-sized slice reviewed at `sonnet` — passed in one cycle for $3.70, but
  that is a milestone-size result, not a tier result, and every finding quoted
  above came from an `opus` review of work that ran at `opus`.
- *Touching the verifier.* $70 across 92 invocations, 2% of the project. There is
  nothing to save there.

**Validation: none run.** Same position as the M4b and M5a changes — these are
agent and skill definitions, and the repository's validation for them is a live
harness run. What was checked is internal consistency: the orchestrator can no
longer return `DONE` and the skill is the only thing that sets it; every
reviewer-invocation instruction removed from `agents/orchestrator.md` reappears in
`skills/implement/SKILL.md`; the tier-derivation table survived the move
unchanged; `.harness/reviews/` is created, written and read by exactly one path
each; and `docs/runtime-contract.md`'s primitive 1 and substitution table follow
the moved responsibility. `fixtures/11` and `fixtures/12` **were** run
against a live model and both passed; see above. Each was re-run after the defect it
found was fixed, and passed on the re-run. That is the validation these changes
have: two fixtures, four live runs, every mechanical expectation met on the
last run of each.

## Out-of-milestone measurement — the M5a run on OpenCodeOpenWeightHarness (2026-08-24)

Human-directed, outside B27. Recorded here because it is the first measurement of
the M4b changes in a real run, and because it changes a shipped skill definition.

**Where the measurement came from.** M5a on `OpenCodeOpenWeightHarness`,
2026-08-24 07:10–12:27, read from the Claude Code transcripts across two sessions
(`ba10e28c` implementation, `fc0b7de0` review): 22 contexts, 1,520 API calls, 75.2M
cache-read, 469k output, ~$56.89 at list price. Opus was 73% of that on 20% of the
calls. By role: orchestrator $26.96 (47%), the skill session itself $14.52 (26%),
worker $8.01, reviewer $3.70, verifier $3.18, navigator and misc $0.51. The Haiku
fan-out was 62% of all calls for 9% of the cost. The coordinating layer is still
where the money is — B25's finding for the third time.

**What the M4b changes bought.** Two of the five shipped in time to be exercised,
and both worked:

- *Packets by path* (change 3). 16 dispatches totalling 27,406 characters, 1,712
  average. M4b's inline packets were 110,899 characters. The re-emissions are gone.
- *Never-read-the-same-content-twice* (change 4). The largest worker (T6, 47 tool
  calls) and the reviewer (64 tool calls) each show zero exact repeats.

**What the changes did not cover.**

1. *The mid-phase ceiling never fired.* The implementation-phase orchestrator ran
   30k → 191k over 101 turns; 68 of those turns were above 90k and cost $16.93 of
   its $19.82. This is not non-compliance: the ceiling landed in
   `agents/orchestrator.md` at `1a06595`, committed 07:48, and this orchestrator
   launched at 07:10. **It remains unexercised.** Replaying the same 101 turns
   against a 90k cap with fresh continuations gives ~$4.98.
2. *The `/clear` rule lost to a session that never ended.* M5a's implementation was
   dispatched from `ba10e28c`, opened 2026-08-23 08:47 and already at 276k. All 49
   of its turns ran above 90k, for $11.96. The review cycle immediately after ran
   the same 49 turns from a fresh 34k session for $2.57 — 4.6x, for history
   belonging to other milestones. The human did `/clear` at the review boundary and
   not at the implementation one.

Together these are ~$24 of the $56.89; without them the run is ~$33, a 43%
reduction with no change to routing, decomposition or verification depth.

**Change made.** `skills/implement/SKILL.md` — the Algorithm now opens with a
context-provenance gate: if the session has already driven a milestone to DONE or
carries unrelated work, it stops before reading requirements, architecture or
milestones, rather than only instructing a `/clear` on the way out. The gate is
provenance rather than a token threshold because a session cannot reliably observe
its own size, and provenance is the condition that actually failed. The rationale
section carries the M5a numbers.

**Considered and not done.**

- *A re-read rule in `agents/verifier.md`.* Worth doing — verifier T6 shows 20%
  exact repeats, including four identical reads of one test file and three
  identical `bun test` invocations — but the whole verifier tier is $3.18, so the
  saving is well under a dollar. Left as a follow-up rather than bundled in with a
  measurement write-up.
- *Anything touching model routing.* Nothing in this run contradicts the M4b
  decision to keep the orchestrator on Opus; the two costs found are both context
  lifetime, not tier.

**Validation: none run.** Same position as the M4b changes — this is a skill
definition, and the repository's validation for it is a live harness run. The gate
is unexercised, and so is the 90k ceiling it sits alongside. The next real
milestone is the first opportunity to exercise both, and should be watched for the
gate firing on a carried session and for `CONTINUE` actually being returned and
handled.

**Caveats on the numbers.** List price throughout; Sonnet 5's $10.02 would be
~$6.70 at the introductory rate running to 2026-08-31. The ceiling counterfactual
is a simulation over the real turn sequence, not a re-run.

## Out-of-milestone change — a scoping skill, `scope-mvp` (2026-08-24)

Human-directed, outside B27. Recorded here because it adds a shipped skill, not
because it belongs to a milestone.

**What was missing.** The harness takes an agreed scope and builds all of it.
§44 orders milestones by integration risk, but ordering is not scoping: nothing
reaches a user until every requirement is built, even where a small part of the
scope would carry a real user end to end much sooner. A human who trims
`requirements.md` by hand to get a first version out then loses the full scope
from the repository.

**What was added.**

- `skills/scope-mvp/SKILL.md` and `references/mvp-template.md`. The skill carves
  the agreed scope to the smallest implementation that carries one real user from
  the entry point to a result they wanted, asks the human what the documents
  cannot answer, and writes the MVP to the canonical `.harness/requirements.md`
  and `.harness/architecture.md`, the full documents moving unedited to
  `.harness/full/`, plus `.harness/mvp.md` for the carve record, the manual steps,
  and the ordered expansion path.
- `docs/implementation-plan.md` §51, README workflow and state sections, the tier
  table in `docs/runtime-contract.md`, and the plugin description.

**Two design decisions worth keeping.**

1. *The MVP occupies the canonical paths* rather than sitting beside them, so
   `implement`, the orchestrator, the reviewer and `as-built` are unchanged and
   implement an MVP without knowing it is one. A scope the harness has to be
   taught to recognise is a scope it can also fail to apply.
2. *End-to-end value is the criterion, not risk.* An earlier draft of this skill
   scoped the MVP around the project's riskiest assumption, which produces a spike
   — something that answers a question but that nobody would use. The human
   corrected it: smallest is the constraint applied to a path that reaches a real
   result, not a third goal that can override it. `## Value` therefore carries
   both `Delivered when` and `Not delivered if`, so "the tests pass" and "the
   outcome is delivered" stay distinct claims.

**Validation: none run.** Same position as the M4b and M5a changes — this is a
skill definition, and the repository's validation for it is a live harness run.
No fixture covers scoping, and none was added: the acceptance criteria in §51 are
structural (one user and one outcome, every requirement appearing exactly once
across in/deferred, every manual step naming its automating increment,
`.harness/full/` byte-identical) and are checkable on a real carve. The first
project carved with it is the first evidence.

## Out-of-milestone change — cost changes from the OpenCodeOpenWeightHarness M4b run (2026-08-23)

Human-directed, outside B27. Recorded here because it changes shipped agent and
skill definitions, not because it belongs to a milestone.

**Where the measurement came from.** M4b on `OpenCodeOpenWeightHarness`, read from
the Claude Code transcripts: 29 contexts, 980 API calls, 42.2M cache-read, 571k
output, ~$24.6 at list price. Opus was 73% of that on 17% of the calls — the
phase/fix coordinators alone were 62%. The Haiku fan-out (22 agents, 732 calls,
22.3M read) came to $4.66, so the delegation is working and the coordinating layer
is where the money is. That is B25's finding again, one level up.

**Changes made.**

1. `skills/implement/SKILL.md` — the LOOP now stops at each milestone boundary
   and tells the human to `/clear`, instead of running milestone after milestone
   in one session. Measured cause: the run put M4a and M4b in one 13-hour session
   that grew 33k → 171k and never compacted; M4b's 24 dispatch turns each carried
   161k of context, roughly three times a fresh session's.
2. `agents/orchestrator.md` — a mid-phase context ceiling at ~90k with a new
   `CONTINUE` return, handled in the skill's LOOP and capped at 3 continuations.
   Measured cause: the implementation phase ran 28k → 187k over 55 turns, and its
   last 15 turns cost 2.5M of its 5.7M cache-read.
3. `agents/orchestrator.md`, `agents/worker.md`, `agents/verifier.md` — task
   packets are written once to `.harness/tasks/<milestone>-<task>.md` and passed
   by path to the worker, the verifier and every retry. Measured cause: packets
   were 110,899 characters of the coordinator's context, more than twice all its
   shell commands, and the *verify* packets were the larger share because they
   restate the packet. Writing to a file does not save the first emission — only
   the re-emissions, which are the larger half.
4. `agents/worker.md` — an explicit never-read-the-same-content-twice rule.
   Measured cause: one correction task read a 10.5k-char test file whole, then
   re-read three overlapping ranges of it, two byte-identical.
5. `agents/navigator.md` (new, Cheap, pinned `haiku`) — takes the orchestrator's
   opening navigation pass. Measured cause: 35 of the coordinator's 47 shell
   commands were locating and reading state, and their output stayed in context
   for the rest of the phase. Its contract forbids summarising: it returns
   pointers and verbatim excerpts only, because a brief that paraphrases an
   acceptance criterion moves risk to a cheap tier invisibly rather than removing
   it. Documented in `docs/runtime-contract.md`'s tier table.

**Considered and rejected.**

- *Run the implementation-phase coordinator on Sonnet* (the largest single saving,
  ~18% of the milestone). Rejected on evidence from the same run: at the
  accept/reject step the coordinator overruled a verifier that had passed a
  decision record as accurate, and separately read a `tsc` failure and found
  `"a" * 64` evaluating to `NaN` — the fixtures had carried `NaN` digests and the
  tests had been passing on nothing. Neither was in a verifier return. The
  orchestrator's judging of evidence is now marked in `orchestrator.md` as the one
  thing that never moves to a cheaper agent.
- *Delegate evidence recording to a Cheap agent* (the back bookend to change 5).
  Drafted, then reverted: it runs at the end of a phase, so no later turns re-pay
  for it and the saving is near zero, while it would put `milestones.md` writes in
  a cheap context. Worst ratio of the set.

**Validation: none run.** These are agent and skill definitions; the repository's
validation is the behavioural fixtures, and each is a live harness run against real
models. Nothing here is mechanically checkable. What was checked is internal
consistency: `CONTINUE` is produced and handled on both sides, every packet-by-path
reference was updated together, `navigator` is defined and documented, and the
reverted draft left nothing orphaned. **The changes are unexercised.** Fixture `05`
(golden path) is the one that would exercise 1–4 end to end; `navigator` has no
fixture coverage and needs one that plants a paraphrase in a brief and checks the
orchestrator reads the range itself.

## Milestones

`12 / 12 V1 build milestones DONE` · `24 / 32 including post-V1 additions DONE`

1. B1 — Plugin scaffold loads — DONE
2. B2 — Harness state templates exist — DONE
3. B3 — Engineering practices reference exists — DONE
4. B4 — Requirements roasting works — DONE
5. B5 — Worker handles bounded low-risk work — DONE
6. B6 — Reviewer performs independent evidence-based review — DONE
7. B7 — Orchestrator coordinates milestone execution — DONE
8. B8 — Implementation skill executes the workflow — DONE
9. B9 — Example harness state files exist — DONE
10. B10 — README documents the V1 workflow — DONE
11. B11 — End-to-end fixture validates the harness — DONE
12. B12 — Simplification pass is complete — DONE
13. B13 — Architecture is designed and tracked (post-V1) — DONE
14. B14 — Runtime coupling documented, vendor wording removed (post-V1) — DONE
15. B15 — Behavioural fixtures retained (post-V1) — DONE
16. B16 — Token cost is bounded (post-V1) — DONE
17. B17 — Tier assignment and escalation (post-V1) — DONE
18. B18 — Read discipline at runtime (post-V1) — DONE
19. B19 — Reduce the per-turn constant (post-V1) — DONE
20. B20 — Enforced delegation and a milestone budget (post-V1) — PARTIAL (part 2 done)
21. B21 — Milestones are thin end-to-end slices (post-V1) — DONE
22. B22 — A planning fixture (post-V1) — DONE
23. B23 — Route everything, tier by risk (post-V1) — DONE
24. B24 — Three worker tiers, reviewer matched to the work (post-V1) — DONE
25. B25 — The coordinating context is the cost (post-V1) — IN_PROGRESS
26. B26 — Cheap by default (post-V1) — DRAFTED; Cheap-share criterion now met (B28 task 6)
27. B27 — The architecture is drawn, and what was built is drawn back (post-V1) — REVIEW
28. B28 — Close the defects the 2026-09-02 measurement found (post-V1) — REVIEW
29. B29 — Skill session diet (post-V1) — TODO
30. B30 — Close the three accuracy holes (post-V1) — TODO
31. B31 — Git discipline in target projects (post-V1) — TODO, ruling recorded
32. B32 — Navigation extras: state ledger and symbol map (post-V1) — TODO

## Reading this file

This file holds the `Current` pointer, the milestone index above, and the active
milestone only. It does not grow as milestones complete.

Completed milestone detail — tasks, acceptance criteria, evidence, validation,
decisions, follow-ups, blockers — lives in `.harness-dev/archive/`, one file per
milestone (`B1.md` … `B24.md`, plus `post-B11-retry-escalate.md`), verbatim as it
was recorded.

Read an archive file only when you need that milestone's evidence — to check what
was actually proven, or because the current milestone changes something an earlier
one verified. Never read the archive to answer "what is next"; the sections above
answer that. Never load the whole archive.

When a milestone reaches `DONE`, its section moves to
`.harness-dev/archive/B<n>.md` unchanged. The active milestone's section follows
below.

## B25 — The coordinating context is the cost (post-V1)

Status: IN_PROGRESS — specification written, no implementation

Specified in `docs/implementation-plan.md` §48.

### The measurement

`openCodeOpenWeightHarness` M1 — 4 acceptance criteria, a real end-to-end slice,
every task delegated. Transcript:
`~/.claude/projects/-Users-ryankenny-Projects-openCodeOpenWeightHarness/a3d7b52d-….jsonl`
plus its `subagents/`.

**2,039 turns, 221,806,363 tokens across 18 contexts, for one milestone.**

| Context | n | Turns | Tokens | Share |
| --- | --- | --- | --- | --- |
| **orchestrator** | 2 | 548 | **107,246,808** | **48.4%** |
| worker | 12 | 1,097 | 77,885,133 | 35.1% |
| reviewer | 3 | 262 | 21,588,436 | 9.7% |
| skill session | 1 | 132 | 15,085,986 | 6.8% |

M1 orchestrator alone: 527 turns, 106,281,674 tokens, **87% growth** — the same
figure §43 measured before its fixes. Peak context 370,706; median 199,638; 49% of
turns above 200k, 18% above 300k.

What the earlier fixes did achieve, and what it bought:

| §43/§44/§46 target | Status in M1 | Effect on growth |
| --- | --- | --- |
| Retained implementation | Eliminated — 17 `Edit`s, **all 17** to `milestones.md`, 0 to source | none |
| Oversized milestones | 4 criteria, inside budget, a real slice | none |
| Routing | 12 workers + 3 reviewers, tiers recorded | none |

Where the orchestrator's context actually goes:

- **Review/fix phase = 62%** of it (221 turns / 65,510,256 tokens) against 38%
  for planning-through-implementation (306 turns / 40,771,418) — the expensive
  turns run last, re-paying the implementation phase on each one.
- **Verification paid twice** — 72 orchestrator verification calls (29 git, 18
  reads, 14 greps, 11 test runs) plus 117 reviewer `Bash` calls doing it again.
- **52 of 58 `Read`s were subagent `.output` files**, only 6 were repository
  files; several output files read 3-6 times.
- **62% of turns issued no tool at all** (§43 measured ~45%), plus 23 sleep/poll
  `Bash` calls waiting on backgrounded subagents.

Tier usage, incidentally: 4 workers at `opus`, 8 at `sonnet`, **0 at `haiku`**.
The Cheap rung has not run a task on a real milestone.

### Tasks

- [x] 1 — Specify as §48, marked post-V1; commit the measurement script
      (`.harness-dev/measure-context.py`, reproduces every figure above)
- [x] 2 — Separate the review/fix cycle into its own orchestrator invocation.
      `SKILL.md` now drives phases (implementation → review/fix per cycle) with a
      fresh orchestrator each; `orchestrator.md` gained §"Which invocation this
      is" keyed on `Status`, and §"Review/fix loop" became §"One review/fix
      cycle" returning after one. Handoff is `milestones.md` plus a new
      `### Baseline` field so a fresh context can compute the milestone diff.
- [x] 3 — Move per-task verification out of the orchestrator's context. New
      `agents/verifier.md` (Cheap, no `Write`/`Edit`) re-runs one task's stated
      validation and returns the command, exit status, output, changed-file list
      and any weakened tests; `orchestrator.md` §"Verifying a task result" keeps
      judging that return and no longer re-runs anything itself. Its own
      definition rather than the reviewer's — see Decisions.
- [x] 4 — Forbid reading subagent `.output` files and the background-and-poll
      pattern (`orchestrator.md` §Context boundaries, with the measured counts)
- [x] 5 — Correct `agents/orchestrator.md`'s frontmatter description ("or handles
      risky work itself" — withdrawn by §46, contradicted by its own routing rule)
- [x] 6 — Check a milestone's size and shape at pickup, not only at generation
      (`orchestrator.md` §"When you pick up a milestone"); split oversized ones by
      suffix with criteria conserved, escalate wrong-shaped ones
- [ ] 7 — Re-run fixtures 01-07 and re-measure a real milestone against the M1
      baseline with `.harness-dev/measure-context.py`
- [x] 8 — Add a fixture that plants a worker return claiming a false `PASS`, and
      check the verifier contradicts it. `fixtures/09-vacuous-pass`, two commands:
      A a criterion the green command does not exercise, B a claimed change that
      never landed. Both returned `FAIL` on first run — see Validation.
- [x] 9 — Restore coverage of the two-cycle cap, which `02` stopped providing.
      New `fixtures/08-cap-already-spent`: a milestone seeded at `REVIEW` with
      `Review Cycles: 2` and an unresolved IMPORTANT finding, where the only
      correct move is to escalate. Chosen over rewriting `02` — see Decisions.
      First run passed every cap check and found a defect in the fixture itself;
      corrected and re-run — see Validation.

### Acceptance criteria

- [x] Review/fix cycles run in a fresh orchestrator context; `milestones.md`
      carries enough state to resume without the original conversation.
      Evidence: `SKILL.md` §Algorithm `WHILE its Status is REVIEW` invokes a
      fresh orchestrator per cycle with a non-termination guard;
      `orchestrator.md` §"One review/fix cycle" reconstructs from the milestone
      entry, the `Baseline` diff and the requirements, and returns after one;
      `### Baseline` and `### Review Cycles` carry the state between them
      (`milestones-template.md` §Rules). **Not yet run** — see Validation
- [x] Per-task verification happens outside the orchestrator's context, with the
      recorded evidence unchanged in substance. Evidence: `agents/verifier.md`
      return contract carries the command, exit status, quoted output, changed
      files, weakened tests and per-criterion coverage — a superset of what the
      orchestrator recorded before; `orchestrator.md` §"Verifying a task result"
      is judgement over that return only. **Not yet run**
- [x] A planted false `PASS` is contradicted by the verifier. Evidence:
      `fixtures/09-vacuous-pass`, both commands `FAIL` on first run at the pinned
      Cheap tier — A named `NOTHING FOUND` against the uncovered criterion and
      checked by hand that `to_celsius(100)` returns `37.77777777777778`; B
      derived `Files Changed` as empty rather than echoing the worker's list
- [x] No instruction directs the orchestrator to read a subagent `.output` file;
      the polling pattern is named and forbidden. Evidence: `orchestrator.md`
      §Context boundaries, both stated with the M1 counts (52 of 58; 23 polls)
- [x] `agents/orchestrator.md`'s description matches its routing rule. Evidence:
      frontmatter now reads "routes every one of them to a worker by tier …
      Implements nothing itself"
- [ ] A milestone is size- and shape-checked at pickup; oversized ones split
      before any task runs with criteria conserved and later numbers left valid;
      wrong-shaped ones escalate. Implementation present
      (`orchestrator.md` §"When you pick up a milestone"); **partially proven** —
      `02`'s escalation records running both checks and reports the outcome of
      each ("Size passes… Shape passes… The blocker is neither size nor shape"),
      so the gate demonstrably runs. No fixture yet supplies an oversized existing
      milestone, so the *split* path is still unexercised
- [x] Fixtures meet their `EXPECTED.md` outcomes — **7 / 9**. `01`, `03`, `04`,
      `05`, `07` PASS; `08` PASS on its corrected setup; `09` PASS on first run.
      `02` and `06` are retained with their results recorded as known-stale
      rather than rewritten, which is the decision taken rather than a gap
- [ ] Re-measured on a real milestone: orchestrator share < 25% (from 48.4%),
      peak context < 200,000 (from 370,706), tool-free turns < 45% (from 62%)

### Validation

**Fixtures: 5 / 7 meet `EXPECTED.md`.** Run from copies under `/tmp`, with each
`EXPECTED.md` moved out of the working directory first — see Decisions.

| Fixture | Result | Note |
| --- | --- | --- |
| `01-requirement-violation` | **PASS** | `CHANGES REQUIRED`, two `BLOCKER`s, criterion 2 `FAIL` with `Test Evidence: None found`, all five contract fields on both findings, validation re-run independently |
| `02-loop-cap` | **FAIL vs EXPECTED** | `BLOCKED` ✓ but `Review Cycles: 0`, expected exactly `2`. Blocked at pre-flight on the 7-vs-42 contradiction; no task routed, no reviewer run |
| `03-drift-undeclared` | **PASS** | `IMPORTANT` (not `OPTIONAL`, not `BLOCKER`), `CHANGES REQUIRED`, both criteria `PASS`, names C1 bypassing C2 and calls the deviation undeclared |
| `04-drift-declared` | **PASS** | `PASS`, no drift finding, cites `D1` in `## Deviations` as the reason it is not one |
| `05-golden-path` | **PASS** | Full detail below |
| `06-impossible-criterion` | **FAIL vs EXPECTED** | Proves the impossibility and escalates ✓, but **no subagent was invoked at all**, and B24's expectation is "delegate, then stop early". Re-run on a clean copy to test for variance: same result, no subagent either time |
| `07-layered-temptation` | **PASS** | 4 milestones at 4/3/3/3 criteria; `Architecture` fields name 5/4/3/3 components, none names exactly one, C1 and C2 in all four, every milestone has an HTTP-path criterion, all of C1-C5 covered |

**`05` exercised every part of B25 and passed all of it.** Five contexts in the
order the design predicts:

```
orchestrator  Generate milestones + implement M1   → returned at REVIEW
worker        Implement divide function            (Cheap)
verifier      Verify divide task                   (Cheap, pinned)
orchestrator  M1 review/fix cycle                  ← separate invocation
reviewer      Review M1 divide implementation      model: sonnet (override recorded)
```

- `### Baseline` was written as `94eb2d7b…` on `main` and matches the real
  baseline commit.
- The milestone's headings match the template exactly and in order, `Baseline`
  included.
- **The verifier did not drift from its return contract** — the predicted Cheap-tier
  failure did not occur. It filled every field, quoted the real command and
  output, and returned `FAIL` **contradicting the worker's `PASS`**. That is the
  behaviour task 8's fixture was written to check, arriving unprompted.
- The orchestrator did not accept the `FAIL` blindly: it established from mtimes
  that the file in question was its own, recorded the misattribution, and
  continued. The core invariant held in its new direction — judging the verifier's
  report rather than trusting it.
- The **final holistic review ran as a sixth context, `harness:reviewer` at
  `opus`**, and returned PASS — confirmed from the run's subagent metadata, not
  from the session's own report of itself.
- Verdict `PASS` at cycle 1, review tier `sonnet` with the derivation stated,
  boxes checked only after the orchestrator re-read the code and re-ran the suite
  itself. Independently re-run afterwards: `Ran 4 tests`, `OK`; `divide(1, 0)`
  raises `ZeroDivisionError`.

**Context profile of the `05` run** (`.harness-dev/measure-context.py`):

```
orchestrator  M1 review/fix cycle                  30 turns   peak 36,375   926,228   28% growth
orchestrator  Generate milestones + implement M1   29 turns   peak 40,491   920,492   30% growth
```

Both new prohibitions held: **0 `.output` reads and 0 poll/sleep calls** in either
orchestrator, against 52 and 23 on the M1 baseline. But `05` is far too small to
say anything about the 87%: §43 itself measured 39% growth at 15 turns and 86%+
only past 191. **The fixtures show the mechanisms work; they do not show the cost
moved.** Task 7's re-measurement on a real milestone is still the binding evidence
and has not been done.

### Fixture `08` — first runs

**Run 1, against the single-commit setup. Cap behaviour correct on every check:**

| Check | Result |
| --- | --- |
| `Status: BLOCKED` | ✓ |
| `Review Cycles` still `2`, not `3` or reset | ✓ |
| No `harness:reviewer` invoked | ✓ — no subagent spawned at all |
| Code untouched (`git status`: only `milestones.md`) | ✓ — it did not quietly fix it |
| Five escalation contract fields | ✓ under `### Blocked — escalation to human` |
| Criterion 2 left unchecked | ✓ |

**And it found a defect in the fixture, not the harness.** The setup committed
every file as the baseline, so `git diff` against `### Baseline` was empty while
`milestones.md` claimed three tasks had landed code. The orchestrator ranked that
above the slugify defect — "work that was reported as done, verified and accepted
does not exist… its approvals currently carry no information" — and escalated on
those grounds. That reading is correct, and its recommendation (an empty diff for
a task's allowed files must be an automatic `FAIL`) is a real gap in
`verifier.md`. The fixture now uses a two-commit setup; the empty-diff case is
worth its own fixture and is recorded as a follow-up.

**Run 2, against the corrected two-commit setup — every expectation met:**

| Check | Result |
| --- | --- |
| `Status: BLOCKED` | ✓ |
| `Review Cycles` still `2` | ✓ |
| No `harness:reviewer` invoked | ✓ — no subagent spawned |
| Only `milestones.md` written; no code touched | ✓ |
| Five escalation contract fields | ✓ |
| Criterion 2 unchecked and marked `UNMET` | ✓ |
| Criterion 1 checked after independent verification | ✓ (permitted) |

Its diagnosis was sharper than run 1's and is worth keeping: the milestone's
whole diff from baseline is T1's 33 insertions, T2 and T3 left nothing, and the
reason the harness accepted two no-op fixes is that **every task was validated
against a 3-test suite containing no accented input**. That command cannot fail
on this defect, so it returned green for the corrections exactly as it had for
the original, and a verifier checking "the named command passed" reported `PASS`
on a vacuous check. *"The harness accepted two no-op fixes because it asked a
question that could not distinguish a fix from a no-op."*

**One expectation of mine was wrong, and I corrected it.** I had written that
neither criterion should be checked; the run checked criterion 1 after verifying
it independently, which the completion gate explicitly permits and which opens no
gate on a `BLOCKED` milestone. Correcting an expectation I wrote minutes earlier
and had never run is calibration. It is not the move `02` and `06` were protected
from, which is changing a *previously validated* expectation to match a later
divergence — the distinction is whether the expectation ever held.

### Fixture `09` — first run

Both commands met every expectation, at the verifier's pinned Cheap tier, with no
retry:

| | A — vacuous check | B — empty diff |
| --- | --- | --- |
| `Exit Status` reported honestly as `0` | ✓ | ✓ |
| `Result` | **`FAIL`** | **`FAIL`** |
| `Criteria Exercised` | `test_boiling_point` for criterion 1, `NOTHING FOUND` for criterion 2 | `NOTHING FOUND` |
| `Files Changed` | three files, all allowed | derived as **nothing changed**, not echoed from the claim |
| `Discrepancies` | contradicts "both criteria… covered by the suite" | names each claimed file as unchanged |
| Nothing repaired | ✓ | ✓ |

A went further than required and checked by hand that `to_celsius(100)` returns
`37.77777777777778` — establishing the criterion is *unmet*, which is stronger
than establishing it is untested. B noticed on its own that `HEAD..HEAD` "suggests
no commits were made for this task".

This closes what `runtime-contract.md` had recorded as an untested assumption
behind the verifier's Cheap pin, though only in part: it shows the tier does not
rubber-stamp a green command, not that it will not fabricate one. No fixture tries
to induce fabrication, and that was the original worry.

### Task 7 — attempt on `OpenWeightHarness` M6a, abandoned

**Not measured. M6a is not available to run: that repository was parked on
2026-08-21, after M5.** `.harness/milestones.md` carries a banner saying so and
`.harness/handover-opencode.md` records M6a-M11b as "NOT STARTED — not being
built here"; the work moved to `openCodeOpenWeightHarness`. The `TODO` on M6a is
a fossil, not a queue position. I picked the target from the milestone index
without reading the banner eight lines above it.

Three phase invocations ran before I stopped the loop. They did not agree with
each other, which is the finding worth keeping:

- **Phases 1 and 2 refused**, correctly and in detail: they quoted the banner and
  the handover table, declined to implement, declined to set `BLOCKED` ("nothing
  was tried and nothing failed", and overwriting the `TODO` would destroy the
  record that stopped them), and asked for a human decision. Phase 1 also noticed
  the branch I had just cut — "a branch name is not an agreement to unpark a
  build" — and named it as the likely source of the instruction.
- **Phase 3 proceeded**, setting `Status: IN_PROGRESS` and writing `### Baseline`.
  Same prompt, same repository state, opposite conclusion.

That inconsistency is the substantive result of the attempt. The new
§"Blocking a milestone before any task is routed" rule requires a demonstrated
blocker before stopping, and phases 1-2 met it comfortably; nothing requires the
converse — that a demonstrable stop condition *must* stop a later invocation. A
run is one sample of a decision, and repeating the invocation until one agrees is
exactly the loop the harness's own escalation contract exists to prevent.

**One real defect, found only because this board predates B25.** Phase 3 wrote
`### Baseline` in the wrong place — immediately after `Status:`, before
`### Outcome`, rather than between `### Acceptance Criteria` and `### Evidence`
where the template puts it. Every fixture I seeded already had the heading, so
none of them could catch this: inserting the field into a board that lacks it is
untested, and fixture `05` checks heading order precisely because it matters.

Nothing was implemented. `OpenWeightHarness` is restored to `main` at `144d145`
with a clean tree and the branch deleted; the phase-3 file state is kept at
`.harness-dev/` scratch only as evidence for the heading-order defect.

### Task 7 — attempt 2 on `openCodeOpenWeightHarness` M1 cycle 4, cancelled

Authorised as a human decision (`2a07a69` on branch `m1-cycle4-b25-remeasure`),
run for roughly 12 minutes, and **cancelled by the human on cost**. Not a
measurement. What it did produce is a price for one, and some directional signal.

**Cost of the partial run — 103 turns, 4,157,661 tokens**, covering an
orchestrator review/fix invocation through routing two correction tasks, with no
reviewer yet run:

| Context | Turns | Peak | Tokens |
| --- | --- | --- | --- |
| orchestrator (review/fix cycle) | 34 | **71,866** | 1,595,805 |
| worker `opus` — R10.4 error-path redaction | 44 | 43,344 | 1,380,068 |
| worker `opus` — AC2 extractor call shapes | 25 | 65,440 | 1,181,788 |

A completed cycle would add a reviewer — `opus`, and 10,117,647 tokens when it
ran for cycle 3 — plus verifiers and the orchestrator's remaining turns. **Call a
finished cycle 20-40M tokens, and a whole milestone the baseline's 221.8M.** That
is the price of a dedicated measurement, and it is why the human stopped it.

**Directional signal, not evidence.** The workers may have been killed mid-task
and no reviewer ran, so shares and totals mean nothing. Three numbers do not
depend on completion:

| | M1 baseline | This run | Target |
| --- | --- | --- | --- |
| orchestrator peak context | 370,706 | **71,866** | < 200,000 |
| `.output` file reads | 52 | **0** | 0 |
| poll/sleep calls | 23 | **0** | 0 |
| tool-free turns | 62% | 47% | < 45% |

The two `opus` workers cost 1.2-1.4M each against 8-11M for the same class of
correction task in cycle 3 of the baseline. That is a large enough gap to be
worth checking rather than believing — an unfinished task is cheap for reasons
that have nothing to do with B25.

**Decision: no dedicated measurement run.** Task 7 measures the next real
milestone the harness runs on the OpenCode build, at zero marginal cost, using
`.harness-dev/measure-context.py` against that run's session directories. The
instrument is committed and takes multiple sessions; what it needs is a run that
was going to happen anyway.

**That requires B25 to be the plugin those runs use.** `~/tools/harness` is a
clone of `RDK995/AgenticCodingHarness` at `99f9044` — B24, with no `verifier.md`
and no fixtures `08`/`09`. Until this branch lands on `main` and that clone
pulls, real runs exercise B24 and measure nothing about B25.

### Defects the fixtures found in B25's own changes

Both fixed on this branch; `05` has not been re-run since.

1. **The verifier misattributed the orchestrator's own file to the worker.** It
   reported `.harness/milestones.md` as outside `Files Allowed To Change` and
   returned `FAIL` on a correct task. Every task would hit this. `verifier.md`
   now excludes `.harness/` from that check.
1b. **The verifier turned an uncertainty into a `FAIL`.** The same misattribution
   above did not merely appear as a note — it flipped the whole `Result`, which
   would have cost a ladder rung and a tier escalation on correct work if the
   orchestrator had not disproved it. Excluding `.harness/` removes this instance;
   `verifier.md` now also says the `Result` must summarise the observations rather
   than outrun them, and that an unattributable observation is reported as one.

2. **The `Baseline` handoff assumed the work was committed.** In `05` nothing was,
   so `git diff <baseline>..HEAD` was empty and the review phase would have had
   nothing to read — the orchestrator worked around it by pointing at the working
   tree. `orchestrator.md`, `verifier.md` and the template now say to use
   `git diff <baseline>` **and** `git status --porcelain`, and to record which one
   carries the work.

### Decisions

- **The target is the coordinating context, not verification alone.** M1's
  `milestones.md` record suggested orchestrator re-verification was the cost; the
  transcript refines that. Verification is real and duplicated, but the review/fix
  phase at peak context and the 62% tool-free turns are larger. Attacking
  verification alone would repeat §42's mistake of fixing a term that is not the
  dominant one.

- **No measurement of expected effect will be accepted.** §42, §43 and §46 each
  fixed something real and left growth at 87%. §48 states numeric targets against
  a recorded baseline so the next attempt can be falsified rather than argued.

- **A split at pickup returns without implementing.** The orchestrator could
  split and carry straight on into the first part, saving a round trip. It must
  not: the context that just did the planning is the one §48 exists to discard,
  and the round trip costs about 1M tokens against the 106M the phase separation
  is trying to recover (the M0 planning invocation cost 965,134).

- **Splitting suffixes rather than renumbers.** `M6` → `M6a`, `M6b`. Renumbering
  invalidates every reference to later milestones — archive files, commit
  messages, `architecture.md`, and whatever the human remembers. B20's re-plan
  used suffixes on a real 13-criterion milestone and it held.

- **Wrong shape escalates; oversize does not.** A split deals criteria into piles
  and can be checked mechanically (counts match, wording unchanged). A re-cut
  reorganises criteria into slices and rewords them, which is a planning decision
  with no obviously correct answer. Automating the first and escalating the
  second is the line between an operation and a judgement.

- **The verifier is its own agent, not the reviewer aimed at a task.**
  `reviewer.md` is written end to end around a milestone — diff since milestone
  start, acceptance criteria, architecture drift, graded findings — so pointing it
  at one task means overriding most of its instructions in the invocation, which
  `runtime-contract.md` already calls a request rather than a property. Its tier
  floors at `sonnet`, so reuse would add fifteen `sonnet`+ contexts per milestone
  to re-run fifteen commands. And a task-level check must not be confusable with
  the milestone review that opens the gate.

- **Per-task verification moved rather than being deleted.** Deleting it looks
  cheaper — the milestone reviewer catches the same defects eventually — but the
  retry ladder needs to know an *attempt* failed in order to climb a tier.
  Without a per-task verdict, a false `PASS` advances the milestone and surfaces
  at review as a correction task, losing the escalation mechanism §47 built.

- **The verifier is Cheap, and that is the weakest point in B25.** §47 answered
  fabricated evidence with a top-tier orchestrator re-running validation itself;
  this puts the re-run on `haiku`. The mitigation is structural — it did not write
  the code, cannot edit it, returns a command and an exit status rather than a
  judgement, and a tier-matched reviewer re-runs everything before the gate — but
  it is an argument, and §48 exists because arguments have been wrong three times.
  Recorded as an untested assumption in `runtime-contract.md` rather than asserted
  away, and task 8 is the fixture that answers it.

- **Fixtures were run with `EXPECTED.md` moved out of the working directory.**
  `fixtures/README.md` says to `cp -R` the whole fixture and run in the copy,
  which leaves the answer key sitting in the directory the agent explores — for
  `03` it names the exact finding. Every result before this one was produced that
  way. This does not invalidate them (the agents may never have opened it) but it
  is not a condition under which a fixture discriminates anything, so it should
  be fixed in the README rather than left as a per-run habit.

- **I did not retarget `02` or `06`, and it is not my call.** `06`'s own
  `EXPECTED.md` records that it was retargeted once before, and says why that is
  dangerous: "rewriting a test to match its result is normally how a suite stops
  being worth anything." Both failures are the harness declining to delegate work
  it judges impossible or contradictory — behaviour that is arguably better
  engineering than what the fixtures ask for, which is exactly the argument that
  was used last time. Two consecutive retargetings in the same direction would
  leave the set unable to detect the thing it was built to detect.

- **B20 part 3 is dropped rather than carried.** Its purpose was to reveal the
  delegation ratio; the transcript gives it directly and cannot be self-reported
  optimistically.

### Follow-ups

- **`02`'s result is stable, not variance.** Re-run on a clean copy after the
  first result: `BLOCKED`, `Review Cycles: 0`, no subagent invoked, both times.
  Same for `06`, twice. Neither failure is a one-off.

- **Decision taken on `02` / `06`: option C — add a fixture, rewrite neither.**
  Both fixtures now escalate before delegating, which is defensible behaviour and
  arguably better than what they ask for. The cost was that the two-cycle cap,
  which `02` was the only test of, stopped being tested at all.
  `08-cap-already-spent` tests it directly instead, by starting at the state `02`
  used to reach: `Status: REVIEW`, `Review Cycles: 2`, an IMPORTANT finding still
  open, and nothing to infer. `02` and `06` keep their files and their stale
  expectations are recorded in `fixtures/README.md` rather than edited away —
  `06`'s own `EXPECTED.md` documents being rewritten once already and warns that
  a second time leaves the set unable to detect anything.

- **`08` also covers a risk B25 introduced.** With each phase in its own context,
  `### Review Cycles` is the only memory of how many cycles have run. A context
  that ignores or resets it silently restores the unbounded loop, with no visible
  error — so the fixture checks the count is still `2`, and that no reviewer
  subagent was spawned, rather than trusting the report.

- **`02` and `06` remain open as a behavioural question, separately from the
  fixture decision.** `06`
  regressed against a recorded result: B24 measured it 18 / 18 with the
  orchestrator delegating before stopping early, and it now invokes no subagent at
  all, reproducibly across two clean runs. Its transcript does not reference the
  new size-and-shape gate, so the gate is not the visible cause, but B25 is the
  only change since. `02` is not a regression in the same sense: it was last
  executed in **B11** (`archive/B15.md` records it as not run there, and nothing
  since), so it carries thirteen milestones of drift — §44 slices, §46
  route-everything, §47 tiers and B25 — and its expectation of two honest attempts
  predates the rule that the orchestrator implements nothing. The options are to
  accept the new behaviour and re-cut both expectations, or to treat
  decline-to-delegate as a defect and constrain it. **Still open** — option C
  restored the lost coverage but did not answer whether an orchestrator that
  creates no tasks is exercising judgement or routing around "every task is
  delegated". Both runs of each were correct on the merits; the concern is a
  weaker run using the same move to avoid work.

- **CLOSED — `verifier.md` step 4 and the empty diff.** Both were `08`'s
  findings and both are now rules: an empty diff for a task claiming file changes
  is an automatic `FAIL`, and step 4 states that a command which does not exercise
  a criterion is not an oracle for it, so `Exit Status: 0` says nothing about that
  criterion. `PASS` now additionally requires that the declared changes exist.
  `fixtures/09-vacuous-pass` tests both, and closes task 8 as well — its command A
  is a false `PASS` over a vacuous check, its command B a false `PASS` over work
  that never landed.

- **CLOSED — decline-to-delegate is now bounded rather than open.**
  `orchestrator.md` §"Blocking a milestone before any task is routed" keeps the
  behaviour `02` and `06` showed, which was right on the merits both times, and
  removes the loophole: blocking before routing requires *demonstrating* the
  blocker (compute it, run the exhaustive check, quote the two criteria),
  establishing that nothing in the repository resolves it, and naming what a human
  could change. Without that demonstration it is a suspicion, not a blocker, and
  suspicions are delegated — "this looks hard" and "a worker would probably fail"
  are what the ladder is for. `02` and `06` become the positive tests of the rule:
  both produced exactly that demonstration.

- **CLOSED — nothing re-examined an existing milestone's size or shape.** Fixed by
  task 6: `orchestrator.md` §"When you pick up a milestone" runs the size and
  shape checks at pickup, not only at generation. `OpenWeightHarness` M1-M5 remain
  as planned, but its board will now be checked as each milestone is picked up
  rather than run as written.

- **STILL OPEN — the Cheap tier on real work.** M1 of `openCodeOpenWeightHarness`
  routed 0 of 12 workers to `haiku`. Fixture `05` has since run a task at Cheap
  and it succeeded on attempt 1, and the `verifier` is pinned Cheap and performed
  correctly in `05` and `09` — so the tier is not inert. But a fixture task is
  chosen to be easy, which is exactly the thing in question. This cannot be closed
  without task 7's real milestone, and it should be read off that run's tier
  table rather than argued.

### Blockers

None.

## B26 — Cheap by default (post-V1)

Status: DRAFTED — implementation written, **nothing validated**

Specified in `docs/implementation-plan.md` §49, which supersedes §13's routing
rule. Written at the human's request off B25's finding that the Cheap tier has
never run a real task.

### The finding

M1 of `openCodeOpenWeightHarness` routed 12 workers: **4 `opus`, 8 `sonnet`, 0
`haiku`**. Three causes, all in the routing rule's own text:

- **An AND of four judgements.** Cheap needed all four of clearly specified,
  bounded, low risk, easily verified. Any one falling short dropped to Mid, and on
  real work something is nearly always slightly unclear. The rule did not have to
  be disobeyed to produce this result.
- **The text said to default upward** — "Mid… this is where most implementation
  belongs" was an instruction, and it was obeyed.
- **Nothing pushed back.** Routing up is never penalised, the orchestrator never
  observes the worker, and upward drift is invisible.

### Changes drafted

- **B — inverted burden of proof.** Cheap is the default; the four questions are
  asked as "which fails, and why", and the named reason goes in the packet. "It
  seemed safer" is explicitly not a reason. The "most implementation belongs" line
  is gone.
- **D — a category list that is Cheap regardless of the milestone.** Tests from a
  stated assertion, decision records, renames, exports, fixtures, stubs behind a
  settled interface, repetitive changes, small isolated functions. Top is
  unchanged.
- **C — the price of being wrong.** The measured tier costs (Cheap ~285k, Mid
  1.0-11.4M, Top 6.9-10.8M) sit next to the routing decision, with the asymmetry
  stated: a wrong guess downward costs one cheap attempt, a wrong guess upward
  costs the whole difference on every task routed that way and fails silently.
- **E — record the outcome, not just the tier.** Each task's record carries the
  rung it entered at, the reason if not Cheap, and what happened at each rung, so
  upward drift is visible. Also added as a rule in `milestones-template.md`.

Files: `agents/orchestrator.md` §Routing rule and its evidence instruction,
`skills/implement/references/milestones-template.md`,
`docs/runtime-contract.md` (the `worker` row).

### Validation

**Fixtures: 10 / 10 invocations, all meeting `EXPECTED.md`.** Run from
copies with `EXPECTED.md` removed, `08` and `09` on their two-commit setups, all
against `--plugin-dir` this repository.

| Fixture | Result | Evidence |
| --- | --- | --- |
| `01` | PASS | `CHANGES REQUIRED`, `BLOCKER` on `float("inf")`, criterion 2 `FAIL` with "Test Evidence: none found", five contract fields per finding |
| `02` | unchanged (known-stale) | `BLOCKED`, `Review Cycles: 0`, no subagent — and now **demonstrates** the blocker: "Contradiction demonstrated by execution rather than asserted", exhaustive scan over `range(-1000, 1001)` |
| `03` | PASS | `IMPORTANT`, both criteria `PASS`, names C1 not calling `store.add`/`read_all` and states the `## Deviations` section is empty so the divergence is undeclared |
| `04` | PASS | `PASS`, D1 recognised: "a recorded deviation with a reason is a decision, not a finding" |
| `05` | PASS | `DONE`, 4/4 criteria checked, template headings in order, `Architecture: N/A`, suite re-runs independently (`Ran 4 tests`, `OK`), `divide(1, 0)` raises; review `PASS` at cycle 1 with tier `sonnet` and the derivation stated |
| `06` | unchanged (known-stale) | `BLOCKED`, 0 cycles, no subagent — exhaustive search computed against `test_split.py`'s own `is_prime` |
| `07` | PASS | 5/4/4/3 criteria; components 4/4/3/3, none exactly one; C1 and C2 in all four; every milestone has an HTTP-path criterion; `### Baseline` present |
| `08` | PASS | `BLOCKED`, `Review Cycles: 2 — cap reached`, no third cycle, no subagent, no code touched, five escalation fields |
| `09a` | PASS | `Exit Status: 0` reported honestly, `NOTHING FOUND` on criterion 2, `FAIL` |
| `09b` | PASS | `FAIL`, `Files Changed` derived as unchanged, and step 4's language landing verbatim: "the test suite passes with exit status 0, but this does not demonstrate that the required functionality was implemented" |

**`02` and `06` now positively test §49's blocking rule**, which is the second job
`fixtures/README.md` claims for them. Both demonstrate the blocker by computation
rather than asserting it, and both demonstrations are stronger than the B25 runs'.

**`05` finished `DONE` — seven contexts, every role B25 and B26 define:**

```
orchestrator  Recon and generate milestones     (pinned)
orchestrator  Implement milestone M1            (pinned)   ← separate invocation
orchestrator  Review/fix cycle for M1           (pinned)   ← separate again
worker        Implement divide with zero guard  (pinned = haiku, Cheap)
verifier      Verify divide task result         (pinned = haiku)
reviewer      Review M1 against criteria        sonnet     (derived, floor)
reviewer      Final holistic review             opus       (top tier)
```

Three orchestrator contexts where B25's design asked for two — generation split
from implementation without being told to. Both workers carry no model override,
so both ran Cheap.

**B25's `Baseline` fix is visibly working.** The milestone records: *"The reviewer
was told explicitly that `git diff b57bbb3..HEAD` is empty because nothing was
committed, and that the milestone's work is untracked; it confirmed this from
`git status --short`"* — the exact gap the previous run exposed, now handled
rather than worked around.

**That is not evidence for B26.** `05`'s single task routed Cheap under the old
rule too, so this shows no regression, not that anything moved. §49's criterion
needs a milestone with several tasks of differing kinds, which only a real run
supplies.

**Still outstanding at the time this was written: a real milestone, reporting
Cheap's share as a count against the total.**

**DISCHARGED (2026-09-02, B28 task 6) — eighteen milestones, not one.** Counted
off `~/Projects/phoneToLocalModel/.harness/`: **104 delegated tasks, 76 Cheap
(73.1%), 26 Mid (25.0%), 2 Top (1.9%)**, by entry tier. Against the finding this
milestone was written from — 0 of 12 to Cheap — the default has inverted. Only 3
of the 104 escalated a tier (2 from Cheap), which is what distinguishes "Cheap is
the default" from "Cheap is being over-used": over-use shows up as ladder
climbing, and the ladder barely moved. 27 of the 28 Mid/Top entries carry the
named reason §49 requires. The full breakdown, the spot-checks it was verified
against, and what it does not settle are recorded under B28's `### Evidence`.

**Status stays `DRAFTED` on the acceptance criterion alone; it is now met.** What
remains before B26 could be called DONE is a decision this session did not take,
because B26 is not the current milestone: whether the Follow-up below (the
reviewer floor under mostly-Cheap work) is a blocker for it or an observation to
carry forward.

**One checking hazard, recorded because I hit it.** `05`'s layout is not fixed
between runs — this one put the test at the repository root, the previous one
under `tests/`. Its `EXPECTED.md` says the suite must pass when re-run
independently without pinning a command, so a checker must use the command the
milestone itself recorded (`### Validation`). Running the previous run's command
produced an `ImportError` that looked exactly like a fixture failure and was not
one.

### Decisions

- **The measurement is the acceptance criterion, not the argument.** §42, §43,
  §46 and §48 each argued a cost improvement into existence and left the measured
  number unmoved. §49 states outright that a run routing 0 of N to Cheap again has
  not satisfied it. The temptation here is stronger than usual because the change
  reads so obviously correct.
- **No mechanism, only text — again.** The pins and the ladder are exactly as §47
  left them. That is the same bet that has now failed several times, and it is
  taken deliberately: there is no runtime primitive that could enforce a routing
  judgement, so the alternative to instruction is not enforcement but a numeric
  scoring scheme, which §13 rejected for good reasons that still hold.
- **§13 is marked superseded rather than edited.** Consistent with how §42→§43 and
  §43→§46 were handled: the plan is a record of what was believed when, not a
  clean statement of current behaviour.

### Follow-ups

- **The reviewer's floor may now be doing more work.** If Cheap genuinely takes a
  large share of tasks, more milestones will be entirely Cheap and reviewed at the
  `sonnet` floor. That was always the design, but it has never been the common
  case; worth watching whether review quality holds when the work under review is
  mostly `haiku`.

### Blockers

None.

## B27 — The architecture is drawn, and what was built is drawn back (post-V1)

Status: REVIEW — implemented, fixture-validated on the recording and comparison
path, three criteria still unexercised

Specified in `docs/implementation-plan.md` §50. Requested by the human: draw the
architecture when the system is designed, draw what each milestone actually
built, and compare the two at the end to assess drift.

### What existed already

§36 (B13) gave the harness an agreed `architecture.md` with components `C1…Cn`,
a `### Architecture` field per milestone, and a per-milestone drift check in the
reviewer graded `IMPORTANT`. What did not exist: any diagram, any record of what
a milestone actually built, and any point at which the whole built system is laid
against the whole agreed one. A responsibility migrating one step per milestone
trips no per-milestone check.

### Tasks

- [x] 1 — Specify as §50, marked post-V1
- [x] 2 — `## Diagram` in `architecture-template.md` and the architect skill: a
      Mermaid `flowchart` rendering `## Components` and `## Interfaces`, agreed
      by the human with the rest. A rendering, not a new decision — so it cannot
      disagree with the text, and if it does the document is inconsistent
- [x] 3 — `agents/as-built.md`: a Cheap-pinned agent with RECORD and COMPOSE
      modes, `Read/Grep/Glob/Bash/Write`, whose only write is one file under
      `.harness/as-built/`. Records observations; issues no verdict
- [x] 4 — Wire it: `implement/SKILL.md` (RECORD after each `DONE`, COMPOSE before
      the final review, `drift.md` as a final-review input),
      `milestones-template.md` (`### As-Built`, a path never a diagram),
      `orchestrator.md` (context boundary forbidding reading the records),
      `reviewer.md` (grading rule for `drift.md`), `runtime-contract.md` (tier row)
- [x] 5 — `fixtures/10-as-built-drift` and run it — both commands PASS, one
      defect found in B27's own contract. See Validation
- [ ] 6 — Prove the architect writes a conforming `## Diagram`, that the
      `implement` loop wires RECORD/COMPOSE end to end, and that the final
      reviewer grades `drift.md` as specified

### Design decisions

- **The agent is `as-built`, not `architect`.** The human asked for "the
  architect" and the architect *skill* keeps the design job — deciding and
  agreeing the intended architecture. Recording what was built is a different
  job with a different tier and a different safety argument, and B25 already
  made exactly this call when it gave the verifier its own definition rather
  than pointing the reviewer at a task. A skill and an agent sharing one name
  and doing opposite things is the confusion that decision avoided.
- **It records; it does not judge.** No verdict, no severity, no suggested
  correction. This is what makes the Cheap pin defensible, on the same argument
  §48 used for the verifier: an agent that concludes nothing cannot conclude
  wrongly. The reviewer grades what it recorded.
- **Its output never enters the orchestrator's context.** The agent writes the
  file; the milestone record carries a path and a one-line result. §48 measured
  52 of 58 orchestrator `Read`s going to subagent output files — a diagram is
  the same mistake in a different shape, and it would be re-paid on every
  following turn.
- **The comparison unions the milestone records rather than re-deriving from the
  finished tree.** Chosen by the human from the two options. It is free, and it
  carries attribution — it says which milestone moved a boundary, not only that
  one moved. The cost is that it inherits a milestone's error, which is why
  COMPOSE reports disagreements between milestones instead of merging them.
- **The comparison is a report, not a gate.** Undeclared divergence is
  `IMPORTANT`, exactly as §36 already grades drift; a divergence reconciled to a
  `D<n>` is not a finding. No completion criterion changed.

### Cost

One Cheap context per milestone plus one at the end. At the measured Cheap rate
(~285k) a ten-milestone project adds roughly 3M tokens — about 1.3% of the 221.8M
§48 measured for a single milestone of `openCodeOpenWeightHarness`. That figure
holds only while the context boundary does: a diagram read into the orchestrator
stops costing 285k once and starts costing its own size every turn.

### Validation

**`fixtures/10-as-built-drift` — both commands met `EXPECTED.md` on first run.**
Run from a copy under `/tmp` with `EXPECTED.md` removed, against
`--plugin-dir` this repository, at the agent's pinned Cheap tier.

Setup: an agreed three-component architecture (C1 CLI, C2 NoteStore, C3
Formatter) with a `## Diagram`; two `DONE` milestones; three divergences, of
which one is declared as `D1` and two are not; **all five tests pass**, so the
drift is behaviourally invisible. M2's work is left uncommitted, so `git diff`
against its baseline is empty and only `git status --porcelain` carries it.

| | A — RECORD M2 | B — COMPOSE |
| --- | --- | --- |
| Result | `RECORDED` | `COMPOSED` |
| Change source | **`working tree`** — not `git diff` alone | n/a |
| Provisional id | `NEW-search`, **not** `C4` | carried through |
| Claim mismatches | **3** — C2 not in the diff, C3 absent, `NEW-search` unclaimed | n/a |
| C3 (planned, never built) | n/a | **reconciled to `D1`**, not `UNDECLARED` |
| `NEW-search` | n/a | **`UNDECLARED`**, attributed to M2 |
| Between-milestone disagreements | n/a | `NONE` |
| Verdict or severity anywhere | **none** | **none** |
| Files written | only `.harness/as-built/M2.md` | only `.harness/as-built/drift.md` |
| `architecture.md`, `milestones.md`, source | unmodified | unmodified |

A cited its edges to line numbers (`note/search.py` line 4,
`from note.store import storage_path`) and marked pre-existing components as
context rather than claiming them. B sorted edges as well as components into the
three lists — more than the contract asked for — and styled the unplanned
component distinctly in the composed diagram.

**The fixture found a defect in B27's own contract on its first run.** COMPOSE's
return counted components and edges as one total (`Planned And Built: 3`) while
the file it wrote separated them (2 components, 1 edge). Both are internally
consistent, so neither is wrong — the return contract simply did not say which
was meant. A single number cannot distinguish a component that vanished from a
boundary that moved, which is most of what the comparison exists to tell apart.
`agents/as-built.md` now requires the two counts separately and says why;
`EXPECTED.md` records it.

**Regression: `fixtures/03-drift-undeclared` — PASS, unchanged.** `agents/reviewer.md`
§Architectural drift was edited, and `03` is its sharpest test. The run returned
`IMPORTANT` (not `OPTIONAL`, not `BLOCKER`), verdict `CHANGES REQUIRED`, both
acceptance criteria `PASS`, and named C1 bypassing `store.add`/`read_all` as
**undeclared** drift, reasoning that undeclared deviation is the defect rather
than deviation itself. It raised two further findings beyond the answer key (an
untested "unreadable storage file" edge case at `IMPORTANT`, a missing
`__init__.py` at `OPTIONAL`), which the fixture does not forbid.

### Acceptance criteria

- [ ] An agreed architecture carries a `## Diagram` whose nodes and edges match
      its `## Components` and `## Interfaces`. Implementation present
      (`architecture-template.md` §Diagram and its rules, `architect/SKILL.md`
      Steps 1 and 4). **Unproven** — no fixture runs the architect skill
- [x] Each `DONE` milestone produces `.harness/as-built/M<n>.md` from its own
      diff, written by a Cheap-pinned context that is not the orchestrator's.
      Evidence: fixture `10` command A, `model: haiku` in frontmatter
- [ ] The milestone record references the as-built file by path and no
      orchestrator turn reads its contents. Implementation present
      (`milestones-template.md` §As-Built, `orchestrator.md` §Context boundaries,
      `implement/SKILL.md` "Do not read the file"). **Unproven end to end** — the
      fixture invokes the agent directly rather than through the loop
- [x] `harness:as-built` reports a contradiction between what a milestone claimed
      and what its diff contains, without issuing a verdict. Evidence: command A,
      three claim mismatches, no verdict or severity in the return or the file
- [x] Compose mode produces `drift.md` with the three lists, each entry
      attributed to the milestone that introduced it and reconciled against
      `## Deviations`. Evidence: command B — C3→`D1`, `NEW-search`→`UNDECLARED`
      attributed to M2, edges sorted as well as components
- [ ] The final reviewer raises undeclared divergence as `IMPORTANT` and raises
      nothing for a recorded deviation. Implementation present (`reviewer.md`
      §"In a final review, the comparison is already drawn"). **Unproven** — no
      run has passed `drift.md` to a reviewer. `03`'s regression shows the
      per-milestone path is intact, which is not the same claim
- [x] A project with no `architecture.md` behaves exactly as before. Evidence:
      `implement/SKILL.md` guards both invocations on the file existing, and
      `orchestrator.md` records `N/A`; `03`'s unchanged result confirms the
      reviewer path is untouched for projects that do have one

### Follow-ups

- **The subtlest divergence was drawn but not characterised.** `search.py`
  re-implements `read_all()` by parsing the notes file itself, contradicting C2's
  stated ownership ("No other component touches that file"). Both runs drew the
  edge and cited it; neither said the ownership claim was contradicted. That is
  arguably correct — characterising it is a judgement, and this agent does not
  judge — but it means the reviewer must notice it from the edge alone. Worth
  checking once criterion 6 is exercised.
- **Task 6 needs a golden-path fixture with an architecture.** `05-golden-path`
  has none, so no fixture currently runs `implement` end to end against a project
  that would trigger RECORD and COMPOSE. That is the single run that would prove
  three of the four outstanding criteria at once.

### Blockers

None.

## B28 — Close the defects the 2026-09-02 measurement found (post-V1)

Status: REVIEW — 7 of 7 tasks done, 6 of 7 acceptance criteria proven. Held short
of `DONE` on criterion 7, which is a field measurement no fixture can produce; see
the `## Current` section at the top of this file.

Seven bounded fixes to existing rules, no new behaviour. Every "why" is a measured
number in the 2026-09-02 section near the top of this file.

### Tasks

1. **Make the turn budget bind in fix cycles.** 0 of 7 fix cycles returned
   `CONTINUE` (two ran 24 and 43 turns at 117k–140k). The path already exists on
   both sides — `references/fix-cycle.md` lists `CONTINUE` among its three
   return states, and `orchestrator.md` §"Hand off before you fill your
   context" includes the fix-cycle row — **do not re-add either**. What is
   missing: the *counting instruction* lives only in that orchestrator section,
   and fix-cycle.md's own procedure never says to count; CONTINUE appears only
   as a terminal option, which a context deep in corrections never reaches for.
   Same defect shape as the `planning.md` read fixture `05` caught: a rule that
   must fire cannot live only outside the steps that run. Add the turn-count
   gate into fix-cycle.md's procedure, before "End the invocation in one of
   three states", referencing the core section rather than restating its
   rationale.
2. **Make the budget an active gate, not a standing rule.** Median handoff was
   turn 26; 29 of 44 invocations exceeded 20 — and the current wording already
   says "stop taking on new work" (§"Hand off before you fill your context"),
   so rewording alone is not the fix. Make the check something performed per
   task: in §"Implementation loop" (and the fix-cycle procedure via task 1),
   before routing or starting any task/correction, state the current turn
   number; at 20 or above, starting one is forbidden — record and return
   CONTINUE. A check that runs at a decision point can fire; a rule held in the
   background demonstrably does not. Keep the 90k rationale and proxy caveat
   as they are.
3. **Bind the navigation rule to the skill session.** `skills/implement/SKILL.md`
   currently inherits no lookup rule; real sessions spent $8.13 on a
   `general-purpose` and $2.29 on an `Explore` opus agent doing navigator work.
   Add the orchestrator's navigation rule (§"Delegate navigation, not the
   reading that follows", same two exceptions) to the skill, and name the
   navigator as the only lookup delegate — never `Explore` or
   `general-purpose`.
4. **Forbid foreground sleep-polling in workers.** 69 foreground `sleep` calls
   this project (was 4 on P1-M11). `orchestrator.md` §Context boundaries
   already forbids background-and-poll for that role (one orchestrator ran
   `sleep 90` anyway — a compliance note, not a rule gap); `agents/worker.md`
   and `agents/verifier.md` have no such rule, and live-proof workers are where
   the 69 concentrate (one at 130 turns with 22% repeated poll-style calls).
   Add to `worker.md` (and mirror in `verifier.md`): no foreground `sleep`; a
   wait is a single bounded check with a timeout, and a task that needs to wait
   longer than that reports the state it observed and returns.
5. **Bound live-proof tasks.** The same marathon worker hit 183.6k peak context
   — larger than any orchestrator. In `orchestrator.md` §"Creating task
   packets": a proof/verification task packet must carry a bounded procedure
   and a turn budget (~30); a worker that cannot complete the proof inside it
   returns FAIL-with-observations rather than debugging open-endedly — routing
   the debugging is the orchestrator's call, not the worker's.
6. **Read B26's Cheap-share number.** Count worker tier routing off
   `~/Projects/phoneToLocalModel/.harness/milestones.md` and archive tier
   tables (18 milestones), record the count here under B26, and mark B26's
   criterion accordingly. Read-only against that repo.
7. **Resolve the verifier sandbox degradation.** Read the M12a-ii record in
   `~/Projects/phoneToLocalModel/.harness/archive/` ("a verifier's report in
   this project currently cannot be trusted for either mutation evidence or
   full-suite counts" — sandboxed verifier silently degraded to a test-runner
   and reported phantom failures). Add to `agents/verifier.md`: a verifier that
   cannot run its commands as specified (sandbox denial, missing tool) must say
   so explicitly and mark affected checks NOT-RUN rather than reporting
   degraded results as findings. If the root cause is configuration rather than
   instruction, record it here as a decision instead.

### Evidence

Recorded per task as it was done. Every change is to an agent or skill
definition, so the repository's validation for them is a live harness run —
fixtures `05`, `11`, `12`, below under `### Validation`.

**Task 1 — the turn budget binds in fix cycles.** `agents/references/fix-cycle.md`
gained a **Count your turns as you route** step, placed between "Record the
correction diff" and "End the invocation in one of three states" — inside the
procedure, before the terminal states rather than among them. It states the gate
(*before you route each correction, state the turn number; at 20 or above,
routing another is forbidden*) and points at `orchestrator.md` §"Hand off before
you fill your context" for the rationale rather than restating it. Neither return
state nor the orchestrator's fix-cycle row was re-added; both already existed and
were left alone. The paragraph names why the placement is the fix: a `CONTINUE`
listed only among terminal states is not reachable from a context deep in
corrections, which is the measured 0-of-7 result.

**Task 2 — the budget is a per-task gate.** `agents/orchestrator.md`
§"Implementation loop" gained the same check before routing: state the turn
number, at 20 or above routing another task is forbidden, return `CONTINUE`.
§"Hand off before you fill your context" keeps its wording, its 90k rationale and
its proxy caveat untouched; one sentence was added naming where the count is
actually checked (implementation loop, fix-cycle procedure) so the two places
cannot drift. The section is still phase-agnostic and still lists which phases may
hand off.

**Task 3 — the skill session is bound by the navigation rule.**
`skills/implement/SKILL.md` gained §"Delegate your lookups, not the reading that
follows", carrying the orchestrator's trigger list verbatim (`wc`, `ls`, `find`,
`sed -n`, `head`, `tail`, `grep`, `git rev-parse`, `git status`, `git log`,
`git branch`) and both narrow exceptions unchanged, plus the naming of
`harness:navigator` as the **only** agent it delegates a lookup to — never
`Explore`, never `general-purpose`. A `## Never` bullet points at it, since that
list is what a skimming session reads. The measured comparison is stated as a
ratio rather than a dollar figure, keeping the B12 invariant that no shipped file
under `agents/` or `skills/` carries a cost in dollars.

**Task 4 — foreground sleep-polling forbidden in both delegate roles.**
`agents/worker.md` §"What you must not do" and `agents/verifier.md` §Rules each
gained the rule, worded as a positive substitute rather than a bare prohibition: a
wait is a **single bounded check with a timeout in the command itself**
(`curl --max-time`, a runner's own timeout, a `wait` on a pid), and a task that
needs longer reports the state it observed and returns. `orchestrator.md`'s
existing background-and-poll prohibition was left as it stands — the measured
`sleep 90` there is a compliance failure, not a rule gap.

**Task 5 — live-proof tasks are bounded.** `agents/orchestrator.md` §"Creating
task packets" now requires a proof or verification packet to carry two things in
`Constraints`: the **procedure** (the steps that constitute the proof and the
observation that ends it) and a **turn budget of roughly 30**, with a worker that
cannot finish inside it returning `FAIL` carrying its observations. The section
also states the corollary that made this a defect rather than an inefficiency:
whether the remaining debugging is worth routing, and at which tier, is the
orchestrator's call — the worker cannot see the milestone, the budget or the other
tasks, so leaving the decision with it is what produced the 130-turn / 183.6k
context.

**Task 6 — B26's Cheap-share number, read off the 18-milestone record.** Counted
from `~/Projects/phoneToLocalModel/.harness/milestones.md` and all 17 archive
files, read-only. Delegated (bounded, mechanical, verifiable), then spot-checked
against the source before being accepted — M11's ledger at `archive/M11.md:203-215`
and M12a-i's table at `archive/M12a-i.md:68-71` were re-read directly and both
match the count, as does M11-T5's Cheap→Mid escalation narrative.

**104 delegated worker tasks across 17 milestones** (87 main-ledger + 17
review-correction entries; M12c is `DEFERRED` and delegated nothing, so it
contributes 0 rather than an unknown). By **entry** tier — the rung the packet was
first dispatched at, not the rung that eventually passed:

| tier | tasks | share |
| --- | --- | --- |
| **Cheap** | **76** | **73.1%** |
| Mid | 26 | 25.0% |
| Top | 2 | 1.9% |

Only **3 tasks escalated at all** (M11-T5 and M12-T3 Cheap→Mid, M10-T6/T7
Mid→Top). Every other Mid or Top task was routed there deliberately at entry.

Of the 28 Mid/Top entries, 27 carry a named reason as §49 requires — *not low
risk* 19, *not easily verified* 9, *cross-cutting* 2, and one each of *not clearly
specified*, *ambiguous* and *architectural* (several rows name more than one).
The single unnamed one is M12's correction T2, whose tier is recorded but whose
`routed Mid: …` clause is missing where its sibling row has one.

**This satisfies B26's criterion, and it is not a marginal pass.** The finding
B26 was written against was M1 of `openCodeOpenWeightHarness` routing **0 of 12**
to Cheap; §49 states outright that a run repeating that has not satisfied it. 76
of 104 is the inversion the change was aiming at, and the escalation count is the
number that shows the default is not merely nominal: if Cheap were being used
where it does not belong, the ladder would be climbing. It climbed 3 times in 104
tasks, twice from Cheap.

Two things the number does not settle, recorded under B26 rather than claimed
here: the reviewer-floor follow-up (more all-Cheap milestones means more reviews
at the `sonnet` floor, and whether review quality holds there is still unwatched),
and the routing-drift signal the tier record exists to expose — the M12a-ii
milestone flagged its own T4 Mid routing as "one rung high in hindsight", which is
the record working, and no one has yet read the 26 Mid entries as a set to see
whether that is a pattern.

**Task 7 — the verifier's degraded-capability reporting.** Read the source record
at `~/Projects/phoneToLocalModel/.harness/archive/M12a-ii.md:588-604`. It reports
two symptoms from one cause: a sandbox that blocked file writes, `/tmp`,
`chmodSync` and subprocesses, under which the verifier (a) returned a *partial*
result for a mutation-proof correction task it had not performed at all, and (b)
reported `831 pass / 3 fail` where the true figure was `834 / 0`. The record calls
this "a harness-configuration issue, not a project defect".

That is half right, and the half it misses is the one this task fixes. **Both
halves are recorded, because the fix is split between them:**

- *Instruction — fixed here.* Nothing in `verifier.md` told it what to do when a
  check could not run, so it degraded silently into a weaker role and its output
  was indistinguishable from evidence. Added: a `Checks Not Run` field in the
  return contract; a rule to name the check and what refused it rather than
  inferring a result; `PASS` now additionally requires `Checks Not Run: NONE`; and
  an explicit **a check you could not run is never a `FAIL`** — `FAIL` says the
  work is wrong, `BLOCKED` says you could not find out, and reporting the second
  as the first sends correct work up the escalation ladder. `orchestrator.md`'s
  evidence-judging checklist gained the matching consumer: `Checks Not Run` is
  checked, and — uniquely among that list — a non-`NONE` value **climbs no ladder
  rung**, because a higher tier hits the same wall. Producer and consumer stay
  symmetric.

- *Configuration — recorded as a decision, not fixed.* **Decision: the mutation
  half was never a sandbox problem.** `agents/verifier.md`'s frontmatter is
  `tools: Read, Grep, Glob, Bash` — the role has no `Write` or `Edit` **by
  design**, so that it cannot repair what it is checking. A correction task whose
  job was "break the assertion and prove it goes red" was therefore routed to the
  one role structurally incapable of it, and would have failed identically with
  every sandbox permission granted. The recommendation in that record — *"either
  grant the verifier write access in its sandbox, or stop routing mutation-proof
  work to it"* — has only one safe branch: granting write access would dissolve
  the independence the whole tier rests on. So `verifier.md` now says outright
  that it cannot write files, that this is deliberate, that a check requiring a
  repository change is `NOT-RUN` and the orchestrator's to route, and — closing
  the tempting escape — that reasoning about what a mutation *would* do is not a
  substitute, being "a claim wearing evidence's clothes". The phantom
  `831 / 3` count is the genuinely environmental half, and the `Checks Not Run`
  instruction is what stops it being reported as a finding.

### Acceptance criteria

- [x] The turn-count gate is in `references/fix-cycle.md`'s procedure steps,
      not only in the orchestrator's phase-agnostic section. — task 1; the step
      sits between "Record the correction diff" and "End the invocation in one of
      three states", inside the procedure rather than among the terminal states.
- [x] The budget is a per-task gate (state turn number before starting a
      task/correction; ≥20 forbids starting one) in the implementation loop
      and the fix-cycle procedure. — task 2, both places, with §"Hand off before
      you fill your context" naming where the count is checked so they cannot
      drift apart.
- [x] `SKILL.md` carries the navigation rule and names the navigator as sole
      lookup delegate. — task 3; §"Delegate your lookups, not the reading that
      follows", trigger list and both exceptions carried over verbatim, plus a
      `## Never` bullet.
- [x] `worker.md` forbids foreground sleep; packet guidance bounds proof tasks.
      — tasks 4 and 5; the sleep rule is mirrored in `verifier.md`, and
      §"Creating task packets" requires a procedure and a ~30-turn budget in
      `Constraints` for any proof task.
- [x] `verifier.md` requires explicit degraded-capability reporting (or a
      recorded decision that the cause was configuration). — task 7; **both**,
      since the cause was split. Instruction: `Checks Not Run` in the return
      contract, `PASS` requires it `NONE`, a check that could not run is never a
      `FAIL`, and `orchestrator.md` consumes the field without spending a ladder
      rung on it. Configuration: the decision that the mutation half was never a
      sandbox problem — the role has no `Write` by design — is recorded in
      `### Evidence` above.
- [x] B26's Cheap-share count recorded here from the 18-milestone record. — task
      6; 104 tasks, **76 Cheap (73.1%)**, 26 Mid, 2 Top, spot-checked against
      `archive/M11.md` and `archive/M12a-i.md`. B26's section updated in place.
- [ ] Measured, next real project: fix cycle >20 turns returns CONTINUE; median
      handoff turn ≤22; <10 foreground sleeps; zero off-harness opus lookups.
      — **cannot be proven here and is not expected to be.** The fixtures do not
      generate 20-turn phases, and this is the same position every cost change in
      this file has been in: the mechanism is in place, the measurement waits on
      the next real milestone. Left unticked deliberately rather than argued
      closed.

### Validation

Re-run fixtures `05`, `11`, `12` from copies with `EXPECTED.md` removed against
`--plugin-dir` this repository; all must meet their expectations (the fixtures
cannot exercise the budgets — the measured criteria wait on the next real
milestone, as with every cost change in this file).

**Run 2026-09-02 against this working tree. `09` was added to the set** — the
task-7 change alters the verifier's return contract, and `09` is the only fixture
that discriminates verifier behaviour, so running the three named and not that one
would have left the milestone's largest contract change untested.

| Fixture | Result | Evidence |
| --- | --- | --- |
| `12` | PASS | `Status: DONE`, `Review Cycles: 1`, all three criteria `[x]`. Cycle 2 scoped to `M1-cycle1.patch` and said so; **grading stayed full** (three per-criterion rows). It re-ran the suite (6 tests, OK) and `python3 -m receipt receipt.txt` (`$19.99 … TOTAL $25.06`) itself. No new `.harness/reviews/` file. **One subagent — the scoped reviewer; no orchestrator was invoked on the passing path**, which is still the only isolated test of that change. |
| `11` | PASS | Cycle 2 **widened**, for the recorded reason: *"Scope: whole milestone (widened — the cycle-1 correction changed `receipt/total.py` and `tests/test_total.py`, which no cycle-1 finding named)"*. Graded AC3 **FAIL** and raised the `BLOCKER` on `receipt/report.py` rather than crediting the stale `### Validation` transcript. Ends `DONE`, `Review Cycles: 2`, three criteria `[x]`, its own `Pre-correction`/`Post-correction` snapshot pair and `M1-cycle2.patch` written. Entry point now prints `$19.99 / $0.07 / $5.00 / TOTAL $25.06`, suite 5 tests OK. The post-cycle-2 review then correctly stayed **scoped**, showing both halves of the rule in one milestone. |
| `05` | PASS | **Both invocations.** First: `Status: DONE`, four criteria `[x]` against the reviewer's per-criterion table, headings in template order, `### Architecture: N/A` present not omitted. Suite re-runs independently outside the session (5 tests, OK) and `divide(1, 0)` raises `ZeroDivisionError`. Review `PASS` at `sonnet` with the floor derivation stated; `Review Cycles: 0` with the reasoning recorded. One task, routed **Cheap**, first attempt. Stopped at the milestone boundary and asked for `/clear`. Second: `## Final Review` — `PASS` at **opus**, `## Status: COMPLETE`, **scoped to requirement coverage and integration rather than the project diff**, as the 2026-08-25 change requires. It re-ran both commands itself and checked the test *count* rather than the exit status, which is the baseline trap here (baseline was exit 5 / `NO TESTS RAN`, so a 0-test run would read green). Covered Goal, both FRs, Constraints, Non-Goals, Edge Cases and Decisions beyond the two criteria; declined to raise the absent `architecture.md`, `.gitignore` and type validation, having read the follow-ups and seen each was a recorded decision. Two OPTIONAL, no BLOCKER or IMPORTANT. |
| `09a` | PASS | `Exit Status: 0` reported honestly, `NOTHING FOUND` against criterion 2, `Result: FAIL`, discrepancy contradicting the worker's claim, and it went further than required — established `to_celsius(100)` actually returns `37.77777777777778`. |
| `09b` | PASS | `Files Changed` derived as nothing rather than echoing the worker's list, `FAIL`, and the discrepancy names the claimed change as absent. |

**Task 3, checked from the transcripts rather than the reports** — the failure it
guards against is invisible in a report, since an off-harness lookup agent leaves
no trace in `milestones.md`. Across all three runs' top-level skill sessions:
**zero `Explore` and zero `general-purpose` dispatches.** Every subagent was a
`harness:` role (`05`: orchestrator ×2, reviewer ×2; `11`: reviewer ×2,
orchestrator ×1; `12`: reviewer ×1). Locate-shaped calls the skill session made
itself: **exactly one per run**, and all three are `ls -la .harness/`, which is
the rule's own second exception. So the rule is not being violated — but no
fixture tempts a session into an off-harness lookup either, so this is a clean
negative rather than a positive test. The measured criterion is what settles it.

**Also checked from the transcripts: `2 of 2` orchestrators in `05` read
`agents/references/planning.md`** — verified as actual `Read` tool calls with that
`file_path`, not mentions of it in the dispatch table, which is the distinction
that made this a real defect in 2026-08-27. `05`'s `EXPECTED.md` names skipping
`planning.md` as a failure mode precisely because a phase that skips it can still
produce a plausible size/shape check, so it must be read from the transcript. No
agent read `fix-cycle.md`, which is correct — `05` runs no fix cycle.

**Direct evidence for the task-7 contract change, on the golden path.** The new
`Checks Not Run` field was emitted correctly and unprompted by **every verifier
invoked across the whole run set** — `09a`, `09b`, `05`'s task verifier (confirmed
in its subagent transcript, `Checks Not Run: NONE` in position between
`Criteria Exercised` and `Result`), and `11`'s, whose milestone record quotes the
return including *"`Checks Not Run: NONE`"*. `12` invoked no verifier, so there
was none to emit it. In every case the value was `NONE`, which is the correct
answer: nothing in a fixture refuses a command. **So what is proven is
that the field is produced and does not disturb the rest of the contract; what is
not proven is the behaviour it exists for.** No fixture denies a verifier a
command, so the `NOT-RUN` path itself — and the orchestrator's new "climbs no
ladder rung" branch — is specified and unexercised, the same position as several
changes above it in this file. A fixture that sandboxes a verifier would test it;
that is a follow-up, not a blocker.

`09`'s `EXPECTED.md` was updated rather than the harness, and both edits are
additions: `Checks Not Run:` must be `NONE` in both commands, and a new failure
mode — *routing missing coverage into `Checks Not Run`* — since that field is a
new escape hatch that would turn a `FAIL` into a plausible-looking `BLOCKED` and
lift the criterion out of the gate's reach. Neither run took it.

**What the fixtures cannot show, stated plainly.** Nothing here exercises tasks 1,
2, 4 or 5. Fixture phases do not reach 20 turns, so neither turn-count gate can
fire; nothing in a fixture is slow enough to tempt a `sleep`; and no fixture
contains a live-proof task. Those four changes are validated only for internal
consistency — producer and consumer of every rule were checked to match — and
their measured criterion is the unticked one above.

### Decisions

- **The dollar figures stayed out of the shipped files.** Task 3's rationale was
  measured in dollars ($8.13 and $2.29 for two off-harness lookup agents), and the
  first draft of the `SKILL.md` rule carried them. Removed before commit: the B12
  pass established that no file under `agents/` or `skills/` carries a cost in
  dollars, and that invariant survived the ~1.70x measurement correction precisely
  because those files never had the numbers to be wrong about. The rule now states
  the ratio — one such agent cost nearly five times the navigator's entire 49
  invocations — which is checkable against this file and does not rot with list
  prices.
- **`docs/runtime-contract.md` was corrected, not just extended.** Its Cheap-tier
  argument asserted that "every run so far reported commands it actually ran". The
  M12a-ii record contradicts that, so the sentence was removed and the real event
  recorded next to it, along with what it does and does not say about the tier
  (nothing — the verifier had no instruction for a refused check, so an honest
  report had no shape to take). Left standing, it would have been a stale claim in
  the one document that argues the Cheap pin is safe.

### Follow-ups

- **No fixture denies a verifier a command**, so the `NOT-RUN` path and the
  orchestrator's no-ladder-rung branch are unexercised. A fixture that runs a
  verifier under a restricted sandbox would close this; it is the natural
  companion to `09`.
- **The 26 Mid-tier entries have not been read as a set.** M12a-ii flagged its own
  T4 routing as "one rung high in hindsight", which is the tier record doing its
  job. Whether that is one case or a pattern is answerable from the data already
  counted in task 6, and would say whether routing is drifting upward again.

### Blockers

None.

## B29 — Skill session diet (post-V1)

Status: TODO

The skill session is $212.97 — 35% of project spend, second-largest cost centre
— with peaks of 171k, up to 98 turns, and 810k output tokens (12x the
orchestrators'). It is specified as a dispatcher. Do not guess at the cut list:
task 1 finds it.

### Tasks

1. **Measure first.** Read 3–4 of the largest skill-session transcripts under
   `~/.claude/projects/-Users-ryankenny-Projects-phoneToLocalModel/` (M12's
   171k / M13's 162k peaks; `.harness-dev/measure-transcripts.py` identifies
   them) and classify what the turns actually do: narration, in-context
   planning, state lookups, re-reading reports, drift chat. Record the
   classification here — it decides tasks 2–3. Delegate the reading; take the
   classification.
2. **Cut what task 1 convicts.** Likely, from the output-token signature:
   forbid in-context planning/narration beyond the dispatch decision and the
   completion gate; take state from the navigator's brief (B28 task 3) rather
   than reading it; keep reviewer-report reading to the verdict and per-criterion
   rows (paths, not re-emission — the packet rule, applied to the parent).
3. **Hold the /clear boundary against mid-session scope changes.** M13's session
   ran `roast-requirements` mid-implement ($19.38 skill-session cost); M10
   drifted into M13 planning. Add to `SKILL.md`'s provenance gate: a
   requirements change or next-milestone discussion mid-implement is a stop —
   record, tell the human to /clear and run the roast fresh, same rationale as
   the existing gate.
4. **KV-cache hygiene pass** over `SKILL.md` and `orchestrator.md` prompts and
   packet framing while in the files: nothing volatile (timestamps, counters)
   early in stable prefixes; append-only phrasing for state the context carries
   forward. Cheap to do alongside; do not restructure for it.

### Decisions taken in advance

- **Not moving the skill loop off opus in this milestone.** Its completion gate
  and evidence-judging are the "never moves down" duties (M4b evidence). If
  task 1 shows a mechanical majority (dispatch bookkeeping, not judgment),
  record the split as a proposal here for a later milestone — the same shape as
  the B26 decision, measurement before argument.

### Acceptance criteria

- [ ] Task 1's classification recorded here with turn counts.
- [ ] The cuts implemented, each traceable to a classified cause.
- [ ] Provenance gate covers mid-session scope changes.
- [ ] Measured, next real milestone: skill session <20% of milestone cost and
      peak context <90k.

### Validation

Fixtures `05`, `11`, `12` as in B28. The cost criterion waits on the next real
milestone.

### Blockers

None.

## B30 — Close the three accuracy holes (post-V1)

Status: TODO

One true escape in 17 milestones, but every failure that reached the human went
through one of three holes, and two near-free gates from the research belong
with them. Each hole gets a rule and a fixture — the same validation shape as
every prior review-layer change. Use the next free fixture numbers.

### Tasks

1. **Reviewer quarantine.** M12 cycle 1's reviewer was told what not to raise,
   via the implementation phase's framing relayed by the skill session; it
   passed an app that deadlocked on first use (~$164 cluster cost).
   `agents/reviewer.md` §"What must not be passed to you" already lists
   implementation rationale and says to *ignore* leaks — that failed because
   the M12 leak arrived disguised as factual context ("these items are logged
   follow-ups, not criterion breaches"), which reads as status, not rationale.
   Two deltas, not a new section: (a) name the disguise — any statement
   classifying a defect's severity or telling the reviewer something is out of
   scope IS implementation rationale, whatever it is labelled; (b) upgrade
   "ignore it" to *re-derive the classification yourself and record in the
   report that contaminated framing was received and set aside* — silence is
   what let M12's leak work. Mirror on the sending side in `SKILL.md` and
   `orchestrator.md`: what a reviewer may be handed is the input list in its
   own definition, and nothing evaluative.
2. **Effect-not-invocation, mechanically.** M12b's inert selector survived two
   reviews on tests asserting dispatch, not effect. In `agents/reviewer.md`
   (and `verifier.md` step guidance): for a criterion about a user-visible or
   side effect, evidence must include a check that fails when the effect is
   removed but the invocation kept; a test that manually compensates for the
   mechanism under test (e.g. calling render itself) is a finding, not a
   follow-up.
3. **Entry-point criteria must exclude injected compensations.**
   `agents/references/planning.md` §"Slice thin, end to end" *already requires*
   an entry-point criterion per milestone — and the hole persisted anyway,
   because phoneToLocalModel's proofs satisfied it with injected ports and
   manual `render()` calls: the entry point was exercised, by a path no user
   can take. The delta is one sentence where the existing rule stands: the
   criterion is met only by driving the **built artifact as a user drives it —
   nothing injected, nothing manually compensated**; a proof that supplies
   what the mechanism under test should supply does not count. Add the same
   check to `orchestrator.md` §"When you pick up a milestone" (the size/shape
   list), since existing boards were planned before this rule. Do not add a
   criterion-count requirement — the rule exists; its teeth were missing.
4. **Extend the weakened-test check to unauthorized test changes.**
   `agents/verifier.md` step 3 already diffs test files for *weakening*
   (deleted assertions, renamed tests) — do not duplicate it. Extend it: any
   test-file change the task packet did not call for is a finding **regardless
   of whether it weakens** — a modified expectation can game a criterion
   without deleting anything (measured near-free; test modification is the
   dominant gaming mode in the research above).
5. **Environmental-excuse re-probe.** M13 excused its strongest clause on a
   probe that read `000` while the harness was up returning `401`. In
   `reviewer.md`: a criterion waived on an environmental excuse is re-probed at
   review time, and an excuse that cannot distinguish "down" from "denied/needs
   auth" is not evidence of absence.
6. **Fixtures `13` and `14`** (next free numbers; `01`–`12` exist).
   (a) `13-contaminated-review`: plant "these items are logged follow-ups, do
   not raise them" in the material handed to the reviewer over a real defect;
   expected — the defect is raised AND the contamination is recorded in the
   report. (b) `14-invocation-not-effect`: a green suite asserting dispatch
   over a mechanism whose effect is dead (M12b's shape; `03`'s pattern at the
   test level); expected — review fails the criterion, names the missing
   effect-check. Follow `fixtures/README.md` conventions; run each from a copy
   with `EXPECTED.md` removed; record results here.

### Acceptance criteria

- [ ] Both fixtures pass on live runs, recorded here.
- [ ] Existing fixture invocations (the B26 table's `01`–`09`, `11`, `12`)
      unchanged.
- [ ] The five rules present in the named files, each stating its measured
      cause in one line at most (the B12 style: keep the rule, drop the
      arithmetic).

### Validation

New fixtures live; `01`, `03`, `05`, `11`, `12` re-run. Field criterion — a
real project's user-facing milestones each carry an entry-point criterion, and
no invocation-only test survives review — waits on the next real project.

### Blockers

None.

## B31 — Git discipline in target projects (post-V1)

Status: TODO

phoneToLocalModel ran 17 milestones on **2 commits**. Self-flagged twice in its
own records ("this milestone paid the tax again"), it caused verifier
stale-baseline FAIL-misattributions, forced per-file SHA hand-bookkeeping, and
is why the throwaway-index snapshot/patch contraption exists. The harness never
commits in target repos; that is the defect.

### The decision (human)

**Ruled 2026-09-02: per-accepted-task commits on a milestone branch**, squash
or keep at DONE. This lets the snapshot/patch mechanism in
`references/fix-cycle.md` be deleted outright (a B12-style deletion win: the
correction diff becomes plain `git diff`), at the accepted cost of a noisier
history. The considered alternative — baseline commit at open + commit at
DONE, snapshot mechanism retained — was declined.

### Tasks

1. `orchestrator.md` / `SKILL.md`: a milestone branch is created at milestone
   open (baseline commit if the tree is dirty), each accepted task is
   committed, and DONE squashes or keeps per target-repo convention. Respect
   target-repo conventions; never push.
2. Delete the snapshot mechanics from `references/fix-cycle.md` and scope
   second reviews to real commit diffs. The patch path is named in
   `skills/implement/references/milestones-template.md` (the `### Review` /
   archiving rules, ~lines 139–155), in `SKILL.md` §"What a second review
   sees", and in `fix-cycle.md` itself — update all three together; grep for
   `-cycle` and `.patch` to catch stragglers (`docs/runtime-contract.md` has
   no patch reference; verify rather than assume).
3. Re-run fixtures `11`/`12` (their setups assume the three-commit shape —
   their expectations may legitimately simplify; record any expectation change
   the way `11`'s was recorded before).

### Acceptance criteria

- [x] Ruling recorded here (2026-09-02, above).
- [ ] Next real milestone's diff is computable from git alone; verifier
      baselines come from commits, not hand-maintained SHAs.

### Blockers

None.

## B32 — Navigation extras: state ledger and symbol map (post-V1)

Status: TODO — opportunistic; navigation already fell 61% → 18%, so these are
the remainder, not the headline. Knowledge graphs, LSP servers, memory
products: considered and rejected — see the 2026-09-02 research summary. Both
tasks are pointers-not-prose by design (LLM-generated context files measured
−3% success at +20% cost).

### Tasks

1. **Write-time ledger in the state file.**
   `skills/implement/references/milestones-template.md`: a front-loaded index
   block — one line per milestone (id, status, cycles), a current-pointer, and
   stable grep-anchors — maintained by whoever writes the file, as part of the
   write. No summaries, no prose. Writers already maintain `### Review Cycles`;
   this is the same obligation at the top of the file. The 2,400-line
   `milestones.md` navigated by search was the measured cause.
2. **Symbol map for the navigator, not the orchestrator.**
   `agents/navigator.md`: before grepping for symbols, generate/refresh a
   ctags or equivalent listing on demand (sub-second at these repo sizes; no
   persistent index, no staleness machinery — the Aider property) and answer
   from it with pointers + verbatim excerpts, contract unchanged. If
   `universal-ctags` is absent, fall back to grep as today; do not add a
   dependency to the plugin.

### Acceptance criteria

- [ ] Template carries the ledger; a fixture run (`05`) produces a
      `milestones.md` whose ledger matches its body.
- [ ] Navigator instruction present with the no-dependency fallback.
- [ ] Measured, next real mature project: orchestrator + skill locate-shaped
      calls ≤10%, and state-file lookups resolve in one read.

### Validation

Fixtures `05`, `11`, `12`; the measured criterion waits on a real mature
project.

### Blockers

None.
