# Harness Implementation Progress

## Current

Milestone: B16 — Token cost is bounded (post-V1)
Task: 6 — run `fixtures/05-golden-path` to confirm harness behaviour is unchanged
by the orchestrator tier pin. Run it in a fresh session.

## Milestones

`12 / 12 V1 build milestones DONE` · `B13 DONE` · `B14 DONE` · `B15 DONE` · `B16 REVIEW`

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
16. B16 — Token cost is bounded (post-V1) — REVIEW

## Reading this file

This file holds the `Current` pointer, the milestone index above, and the active
milestone only. It does not grow as milestones complete.

Completed milestone detail — tasks, acceptance criteria, evidence, validation,
decisions, follow-ups, blockers — lives in `.harness-dev/archive/`, one file per
milestone (`B1.md` … `B15.md`, plus `post-B11-retry-escalate.md`), verbatim as it
was recorded.

Read an archive file only when you need that milestone's evidence — to check what
was actually proven, or because the current milestone changes something an earlier
one verified. Never read the archive to answer "what is next"; the sections above
answer that. Never load the whole archive.

When the active milestone below reaches `DONE`, move its section to
`.harness-dev/archive/B<n>.md` unchanged and replace it here with the next
milestone.


## B16 — Token cost is bounded (post-V1)

Status: REVIEW

Specified in `docs/implementation-plan.md` §39. Requested after measured token
spend on this repository's own build was judged too high. Bounds how long a
context lives; changes no harness behaviour.

### Tasks

- [x] Specify as `docs/implementation-plan.md` §39, marked post-V1
- [x] Split `.harness-dev/progress.md` history into `.harness-dev/archive/`, losslessly
- [x] Add Context Discipline to `CLAUDE.md` — session boundaries, delegation default, ranged reads
- [x] Name every subagent role's model tier in frontmatter
- [x] Apply the same archiving rule to the runtime `.harness/milestones.md`
- [ ] Run `fixtures/05-golden-path` to confirm behaviour is unchanged

### Acceptance Criteria

- [x] The session-start read is bounded and does not grow with completed milestones. Evidence: `progress.md` 952 → 47 lines (8254 → 318 words) plus the active milestone; Check 3.
- [x] Completed milestone detail retained in full and reachable, proven by reconstruction. Evidence: 16 archive files reconstruct `HEAD:.harness-dev/progress.md` lines 31-952 byte-identically, 59,605 chars both sides; Check 1.
- [x] The protocol states when to end a session and when to delegate. Evidence: `CLAUDE.md` §Context Discipline (3 subsections), protocol steps 14-15.
- [x] Specification reads are section-scoped, with the mechanism stated. Evidence: `CLAUDE.md` step 3 (`grep -n` then `sed -n 'A,Bp'`), §Context Discipline "Read in ranges".
- [x] Every role's model tier is named in a file and matches `runtime-contract.md`. Evidence: worker `haiku`/Cheap, orchestrator `sonnet`/High, reviewer `opus`/Highest; Checks 5 and 6.
- [x] The reviewer is not downgraded. Evidence: `agents/reviewer.md` frontmatter `model: opus` — pinned up from session-inherited, not down.

### Evidence

- `docs/implementation-plan.md` §39 — measured problem, solution, scope, criteria
- `.harness-dev/archive/` — B1-B15 plus `post-B11-retry-escalate.md`, verbatim
- `.harness-dev/progress.md` — Current, index, "Reading this file", active milestone only
- `CLAUDE.md` — §Context Discipline; protocol steps 1, 3, 14, 15; Sources of Truth
- `agents/orchestrator.md` — `model: sonnet`; §Context boundaries; archiving in §Recording completion evidence
- `agents/reviewer.md` — `model: opus`
- `skills/implement/references/milestones-template.md` — §Archiving completed milestones
- `skills/implement/SKILL.md` — final review reads archived outcomes
- `docs/runtime-contract.md` — substitution table rows per tier; fixture pointer corrected

### Validation — 9 / 9 structural checks PASS

| # | Check | Result |
| --- | --- | --- |
| 1 | Archive reconstructs committed history byte-identically (59,605 chars) | PASS |
| 2 | `Current` pointer and milestone index survived the split | PASS |
| 3 | Session-start read 952 → 47 lines | PASS |
| 4 | All 16 archived sections present and reachable | PASS |
| 5 | All 6 plugin components discoverable, frontmatter valid | PASS |
| 6 | Pinned models match the `runtime-contract.md` tier table | PASS |
| 7 | Milestone template block byte-unchanged (fixture 05 asserts heading order) | PASS |
| 8 | No broken repo-internal path references | PASS |
| 9 | Archive tracked by git, not ignored | PASS |

Check 7 detail: `git diff` on the template shows one deleted line — the "No JSON
state store" rule, reworded to admit the archive. The fenced `markdown` milestone
block that fixture 05 checks is byte-identical; heading order unchanged.

**Not yet run:** `fixtures/05-golden-path` end to end. This is the check B14 used
to prove behaviour was unchanged, and it is the one that would exercise the
orchestrator on its new tier. Until it runs, "behaviour unchanged" is reasoned,
not proven — which is why this milestone is `REVIEW` and not `DONE`.

### Decisions

- **Orchestrator pinned to `sonnet`, reviewer to `opus` — the opposite of the
  initial proposal.** The first suggestion was to run the reviewer cheaper. That
  contradicts `runtime-contract.md`, which puts the reviewer at the **Highest**
  tier and names it "the one to protect": a weak reviewer does not fail loudly, it
  emits a confident `PASS`, and the gate then opens on nothing. The tier table
  already assigned orchestrator High and reviewer Highest; this pins each role to
  the tier it was assigned instead of inventing a new mapping. The saving comes
  from the orchestrator, which runs many turns per milestone.
- **Pinning is the point, not just the value.** Before B16 the orchestrator and
  reviewer inherited the session model. That silently downgrades the reviewer on a
  cheap session — the exact failure `runtime-contract.md` warns about — and
  overpays for the orchestrator on an expensive one. A role's tier should be a
  recorded decision, not a side effect of how the session started.
- **Archive split is a move, never a summary.** Completed evidence is the record of
  what was actually verified; summarising it would destroy the thing the repository
  exists to protect. Proven by reconstruction against git rather than asserted.
- **Runtime archiving is threshold-gated at ~400 lines.** Unconditional archiving
  would break `fixtures/05-golden-path`, which requires a completed single-milestone
  `milestones.md` to carry every template heading in order. Short projects archive
  nothing.
- **No token accounting, budgets, or configuration added.** V1 excludes workflow
  infrastructure. The changes are instructions, state layout, and three frontmatter
  lines.
- **`.claude/RESUME.md` left alone.** It is a Claude Code checkpoint artifact under
  a gitignored directory, not harness state.

### Follow-ups

- Run `fixtures/05-golden-path` end to end and record the result; promote this
  milestone to `DONE` only then. If the orchestrator on `sonnet` degrades routing
  or independent verification, change one frontmatter line back to `opus` — the
  substitution point is documented in `runtime-contract.md`.
- The measured 84%-of-spend-above-100k figure came from reading this project's own
  session transcripts. Worth re-measuring after a few milestones under the new
  protocol to confirm the boundary rule is actually being followed, rather than
  assuming it is.
- `docs/implementation-plan.md` is 1705 lines and every session reads part of it.
  If section-scoped reads prove insufficient, splitting it per phase is the same
  move applied one level up. Not done now: no evidence yet that it is needed.

### Blockers

None.
