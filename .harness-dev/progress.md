# Harness Implementation Progress

## Current

Milestone: B25 — The coordinating context is the cost (post-V1)
Task: 7 — re-measure a real milestone. It is the only task left, and the only
acceptance criterion with no evidence. **Needs a target**: `OpenWeightHarness` is
parked and cannot supply one (see Validation), so the candidates are unparking
that repo or a live milestone in `openCodeOpenWeightHarness`, whose M1 is
`BLOCKED` awaiting a human decision and whose M2 is `TODO`.
Status: IN_PROGRESS (8 of 9 tasks done; 5 of 7 acceptance criteria proven).
Every follow-up is closed except the Cheap tier on real work, which task 7
answers by measurement rather than argument.

Open: B20 part 3 (recording tasks planned vs delegated) — superseded in practice.
The M1 measurement below reads the delegation ratio straight from the transcript,
which is stronger than a self-reported count.

## Milestones

`12 / 12 V1 build milestones DONE` · `24 / 25 including post-V1 additions DONE`

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
