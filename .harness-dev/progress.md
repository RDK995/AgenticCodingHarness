# Harness Implementation Progress

## Current

Milestone: none active. All 17 build milestones are `DONE`.

There is no next task. The harness is complete against
`docs/implementation-plan.md` §§1-40. Open items are recorded as follow-ups in
the archive, not as work in progress — read `.harness-dev/archive/B17.md`
(§Follow-ups) and `.harness-dev/archive/B16.md` (§Follow-ups) before starting
anything new. The largest of them: the runtime `implement` skill still loops
every milestone in one driving session, and the worker tier ladder is unexercised
by any fixture (waived, `docs/implementation-plan.md` §40).

## Milestones

`12 / 12 V1 build milestones DONE` · `17 / 17 including post-V1 additions DONE`

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

## Reading this file

This file holds the `Current` pointer, the milestone index above, and the active
milestone only. It does not grow as milestones complete.

Completed milestone detail — tasks, acceptance criteria, evidence, validation,
decisions, follow-ups, blockers — lives in `.harness-dev/archive/`, one file per
milestone (`B1.md` … `B17.md`, plus `post-B11-retry-escalate.md`), verbatim as it
was recorded.

Read an archive file only when you need that milestone's evidence — to check what
was actually proven, or because the current milestone changes something an earlier
one verified. Never read the archive to answer "what is next"; the sections above
answer that. Never load the whole archive.

When a milestone reaches `DONE`, its section moves to
`.harness-dev/archive/B<n>.md` unchanged. No milestone is active, so this file
currently holds the pointer and the index only.
