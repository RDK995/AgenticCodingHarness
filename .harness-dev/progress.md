# Harness Implementation Progress

## Current

Milestone: B25 — The coordinating context is the cost (post-V1)
Task: 7 — re-measure a real milestone (fixtures are run; 5 / 7 meet EXPECTED)
Status: IN_PROGRESS. Two fixtures do not meet their `EXPECTED.md` and neither is
safe for me to retarget — see Validation. A human decides what `02` and `06`
should now expect.

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
- [ ] 8 — Add a fixture that plants a worker return claiming a false `PASS`, and
      check the verifier contradicts it. Blocks `DONE`: without it the verifier's
      Cheap pin is an untested assumption, which `runtime-contract.md` currently
      says outright.

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
- [ ] A planted false `PASS` is contradicted by the verifier (task 8)
- [x] No instruction directs the orchestrator to read a subagent `.output` file;
      the polling pattern is named and forbidden. Evidence: `orchestrator.md`
      §Context boundaries, both stated with the M1 counts (52 of 58; 23 polls)
- [x] `agents/orchestrator.md`'s description matches its routing rule. Evidence:
      frontmatter now reads "routes every one of them to a worker by tier …
      Implements nothing itself"
- [ ] A milestone is size- and shape-checked at pickup; oversized ones split
      before any task runs with criteria conserved and later numbers left valid;
      wrong-shaped ones escalate. Implementation present
      (`orchestrator.md` §"When you pick up a milestone"); **unproven** — no
      fixture exercises an oversized existing milestone yet
- [ ] Fixtures 01-07 meet their `EXPECTED.md` outcomes — **5 / 7**. `01`, `03`,
      `04`, `05`, `07` PASS; `02` and `06` do not, and are a human decision
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

### Defects the fixtures found in B25's own changes

Both fixed on this branch; `05` has not been re-run since.

1. **The verifier misattributed the orchestrator's own file to the worker.** It
   reported `.harness/milestones.md` as outside `Files Allowed To Change` and
   returned `FAIL` on a correct task. Every task would hit this. `verifier.md`
   now excludes `.harness/` from that check.
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

- **`02` and `06` need a human decision, and they are different cases.** `06`
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
  decline-to-delegate as a defect and constrain it. Do not decide it from one
  run of each.

- **The Cheap tier has never run a real task** (0 of 12 workers at `haiku`).
  Either §47's Cheap criteria never match real work, or routing is defaulting
  upward. Worth measuring before concluding the tier is useless.
- **`OpenWeightHarness` M1-M5 predate §43/§44** and were never re-cut; M5 ran at
  7 criteria on one component (C9) with no entry-point criterion. Nothing
  re-examines an existing milestone's size or shape before running it —
  `SKILL.md` picks the first non-`DONE` milestone and runs it, and the slice and
  budget rules are subsections of §"Generating milestones", which only fires when
  `milestones.md` is absent. A separate concern from §48; record it if it bites.

### Blockers

None.
