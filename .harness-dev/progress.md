# Harness Implementation Progress

## Current

Milestone: B21 — Milestones are thin end-to-end slices (post-V1) — DONE
Task: none active. B20 parts 1 and 3 remain open (tool restriction; delegation
record) — see `.harness-dev/archive/B20.md`.

## Milestones

`12 / 12 V1 build milestones DONE` · `21 / 21 milestones` · `B20 part 1+3 outstanding`

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

## Reading this file

This file holds the `Current` pointer, the milestone index above, and the active
milestone only. It does not grow as milestones complete.

Completed milestone detail — tasks, acceptance criteria, evidence, validation,
decisions, follow-ups, blockers — lives in `.harness-dev/archive/`, one file per
milestone (`B1.md` … `B21.md`, plus `post-B11-retry-escalate.md`), verbatim as it
was recorded.

Read an archive file only when you need that milestone's evidence — to check what
was actually proven, or because the current milestone changes something an earlier
one verified. Never read the archive to answer "what is next"; the sections above
answer that. Never load the whole archive.

When the active milestone below reaches `DONE`, move its section to
`.harness-dev/archive/B<n>.md` unchanged and replace it here with the next
milestone.


## B21 — Milestones are thin end-to-end slices (post-V1)

Status: DONE

Specified in `docs/implementation-plan.md` §44. The harness was generating
component-shaped milestones because `agents/orchestrator.md` taught that shape in
two places.

### The cause

The section labelled `Good:` was a layer sequence — domain model, then API, then
persistence — in which nothing is demonstrable until the last milestone. And the
coverage gate said milestones "realise" components, each `### Architecture` field
lists "the component ids it realises", and "every component must be realised by at
least one milestone" — mapping milestones onto components roughly one-to-one, which
produces a layered plan by construction whatever the examples say.

On the real project this produced 21 components' worth of component milestones with
all integration deferred into one 12-criterion milestone at the end.

§43's criteria budget does not fix this and can worsen it: splitting an oversized
component milestone yields smaller *component* milestones — thinner, no more
demonstrable. B20's M6 split did exactly that.

### Tasks

- [x] Specify as §44, marked post-V1
- [x] Replace the worked example with a walking skeleton; demote the old one to `Bad`
- [x] Require an entry-point criterion per milestone
- [x] Reconcile the coverage gate — advance/exercise rather than realise
- [x] State ordering by integration risk, and the boundary safeguard
- [x] Validate by re-cutting real component milestones, and re-run fixtures 03/04

### Acceptance Criteria

- [x] Worked example is a walking skeleton. Evidence: `agents/orchestrator.md` — three API-demonstrable milestones under `Good`; the previous layer sequence now appears under `Bad — layers. Nothing is demonstrable until the last one.`
- [x] Demonstrability rule stated, naming the real entry point. Evidence: §"Slice thin, end to end" — CLI invocation, HTTP request, public API call; "if the only way to demonstrate a milestone is a unit test of an internal component, it is a component milestone and must be re-cut."
- [x] Coverage gate permits a component advanced across several milestones. Evidence: field lists ids the slice **advances**; gate is now "every component must be **exercised** by at least one milestone", with an explicit warning that one-to-one mapping produces a layered plan.
- [x] Ordering by integration risk stated. Evidence: "Order slices by integration risk, not by convenience."
- [x] Boundary safeguard stated where slicing is taught. Evidence: "Thin is not a shortcut through the architecture… A slice crosses every boundary the architecture defines; it crosses each one shallowly."
- [x] Re-planned on real component milestones; result is slices with scope conserved. Evidence: Validation below.
- [x] Fixtures 03 and 04 unchanged. Evidence: Validation below.

### Validation — re-cut of M6-M9 on a copy of the real project

Planning only; no source file touched (copy stayed at its baseline 12 dirty files).

| Before (component-shaped) | After (behaviour-shaped) |
| --- | --- |
| Read-only and git-query tools answer through one registry (2) | A question about a real repository **is answered** through the registry (5) |
| Commands and tests run only through a sandbox seam (4) | A command **runs** against a real worktree through the sandbox seam (5) |
| The full FR4 vocabulary mutates files, stays in worktree (4) | An edit **changes a file** in a real worktree through the registry (5) |
| Every mutation runs the pipeline and rolls back (3) | A failing edit **rolls back** and leaves the worktree as it was (3) |

**Every slice carries exactly one `**Entry point:**` criterion** — the rule landed
more checkably than specified, since they are labelled and therefore greppable.

**The `### Architecture` fields are the clearest evidence:**

```
M6: C10 (advances; also exercises C4, C6, C7, C9)
M7: C21, C10 (advances; also exercises C4, C6, C7)
M8: C10, C11 (advances; also exercises C4, C6, C7)
M9: C11 (advances; also exercises C6, C9, C10)
```

Each slice touches 4-7 components shallowly rather than realising one, and C10 is
advanced by three separate slices — the behaviour the old wording forbade.

**Criteria went 13 → 18, and that is demonstrability rather than scope creep.**
Four criteria appeared to be "lost" by fuzzy match; each was reworded or split, not
dropped — "classified by the policy engine first" survives in M6; the sandbox-seam
criterion split into M7's entry point plus a separate timeout criterion; the
`validate → checkpoint → apply` chain became M9's entry point. The +5 is four
entry-point criteria plus one compound criterion split in two.

### Validation — fixtures 03 and 04

Both pass; the drift pair still works in both directions.

- **03** — verdict `CHANGES REQUIRED`, `BLOCKER (none)`, drift graded `IMPORTANT`, both criteria `PASS`. Names it precisely: "C1 bypasses C2, persistence logic is duplicated/dead-code split between `note/cli.py` and `note/store.py`, and `architecture.md`'s `## Deviations` does not record it."
- **04** — no drift finding; both criteria `PASS`; states "the declared architectural deviation is properly recorded and not itself a defect". Its only `IMPORTANT` is the unhandled malformed-storage-file bug that `EXPECTED.md` says is real and deliberate.

Recorded honestly: my first check of 03 reported a `BLOCKER` that did not exist — the
grep matched the section header above `(none)`. Second false positive of this kind
today; the checks, not the harness.

Also recorded: 03 and 04 invoke the reviewer directly and B21 changed only
`orchestrator.md`, so by construction they cannot exercise this change. They are a
no-accidental-breakage check. The re-cut above is the validation that bears on B21.

### Decisions

- **The old `Good` example is demoted to `Bad`, not deleted.** It is the shape most
  plans default to, so naming it as the anti-pattern teaches more than removing it.

- **The coverage gate had to change or nothing else would matter.** Examples advise;
  a gate checked before generation finishes decides. While it required every
  component to be *realised* by a milestone, the slicing guidance would have been
  overridden at the point of enforcement.

- **The boundary safeguard sits in the slicing section, not only under Architecture.**
  Slicing creates pressure to bypass a seam for the shortest working path, which is
  exactly `fixtures/03-drift-undeclared`. The warning belongs where the pressure is
  created.

### Follow-ups

- **The project's remaining milestones are still component-shaped or oversized.**
  M10 carries 12 criteria and is the integration milestone; M4, M5 and M11-M14 carry
  7-9. Only M6-M9 were re-cut.
- **Fixture 05 was not re-run under B21 before merge.** It exercises generation,
  which B21 changes; it was run concurrently with the merge rather than before it.
- **No fixture asserts slice shape.** Nothing in the retained set fails if the
  harness reverts to layered milestones. The demonstrability rule is greppable
  (`Entry point:`), so a fixture could check it — none does.

### Blockers

None.
