# Harness Implementation Progress

## Current

Milestone: B25 — The coordinating context is the cost (post-V1)
Task: 3 — move per-task verification out of the orchestrator's context
Status: IN_PROGRESS (tasks 1, 2, 4, 5, 6 done; 3 and 7 remain)

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
- [ ] 3 — Move per-task verification out of the orchestrator's context; decide
      whether it reuses the reviewer or needs its own definition
- [x] 4 — Forbid reading subagent `.output` files and the background-and-poll
      pattern (`orchestrator.md` §Context boundaries, with the measured counts)
- [x] 5 — Correct `agents/orchestrator.md`'s frontmatter description ("or handles
      risky work itself" — withdrawn by §46, contradicted by its own routing rule)
- [x] 6 — Check a milestone's size and shape at pickup, not only at generation
      (`orchestrator.md` §"When you pick up a milestone"); split oversized ones by
      suffix with criteria conserved, escalate wrong-shaped ones
- [ ] 7 — Re-run fixtures 01-07 and re-measure a real milestone against the M1
      baseline with `.harness-dev/measure-context.py`

### Acceptance criteria

- [x] Review/fix cycles run in a fresh orchestrator context; `milestones.md`
      carries enough state to resume without the original conversation.
      Evidence: `SKILL.md` §Algorithm `WHILE its Status is REVIEW` invokes a
      fresh orchestrator per cycle with a non-termination guard;
      `orchestrator.md` §"One review/fix cycle" reconstructs from the milestone
      entry, the `Baseline` diff and the requirements, and returns after one;
      `### Baseline` and `### Review Cycles` carry the state between them
      (`milestones-template.md` §Rules). **Not yet run** — see Validation
- [ ] Per-task verification happens outside the orchestrator's context, with the
      recorded evidence unchanged in substance
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
- [ ] Fixtures 01-07 meet their `EXPECTED.md` outcomes
- [ ] Re-measured on a real milestone: orchestrator share < 25% (from 48.4%),
      peak context < 200,000 (from 370,706), tool-free turns < 45% (from 62%)

### Validation

**Not yet run.** Nothing here is proven; the text changes are implementation, not
evidence. Two things must run before any of it counts:

- Fixtures 01-07. `02` and `06` drive the orchestrator directly and their
  single-shot `-p "Run milestone M1 to completion"` cannot reach a review cycle
  now that phases are separate; both were changed to a per-phase loop, which is
  the change most likely to have broken something.
- The re-measurement, which is the binding one.

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

- **B20 part 3 is dropped rather than carried.** Its purpose was to reveal the
  delegation ratio; the transcript gives it directly and cannot be self-reported
  optimistically.

### Follow-ups

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
