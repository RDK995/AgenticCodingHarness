# Planning a milestone

Read this on a **planning phase**, or when generating milestones. An
implementation phase never needs it — it runs a plan a human already agreed —
and neither does a fix cycle.

Reconnaissance and the size/shape check run on every milestone's first planning
phase. "Generating milestones" runs once per project — only when
`.harness/milestones.md` does not exist yet.

## Repository reconnaissance

Before generating milestones (and again, lightly, before planning tasks for a
milestone), do a lightweight inspection — don't spawn another agent for this,
and don't produce a large recon document. Determine only:

```
Architecture
Relevant files/modules
Existing conventions
Test framework
Build commands
Lint/type-check commands
Likely integration points
Material risks
```

This exists to make milestone/task planning better, not to be an artifact in
itself. Milestones must account for existing architecture, existing testing
patterns, existing public interfaces, and relevant integration boundaries.

## Generating milestones

If `.harness/requirements.md` exists and `.harness/milestones.md` does not,
generate milestones into it using **exactly** the structure in
`${CLAUDE_PLUGIN_ROOT}/skills/implement/references/milestones-template.md` — same headings
(`### Outcome`, not a renamed or added heading), same order, nothing extra.
Reconnaissance is a planning input, not persisted state: use it to shape the
milestones, but do not write a reconnaissance section into `milestones.md`
itself. The file holds milestones only. In the same planning step, write
`.harness/state.json` using schema version 1 and the shape in
`${CLAUDE_PLUGIN_ROOT}/examples/state.example.json`. Map every in-scope
requirement id to one owning milestone and give every acceptance criterion a
stable `<milestone>-AC<n>` id. Validate both files with `python3
${CLAUDE_PLUGIN_ROOT}/scripts/check-state.py .harness/state.json --milestones
.harness/milestones.md --requirements .harness/requirements.md` before returning;
generation is incomplete if they disagree.

Milestones represent **observable outcomes**, not implementation steps. Tests
belong inside each milestone, not as a separate milestone.

### Extending the milestones

An existing project grows by new requirements, agreed through
`roast-requirements` after its milestones were made. The `plan` skill passes you
the ids no milestone owns. Generate milestones for **exactly those**, by every
rule below — thin vertical slices, sized, ordered by integration risk — with
three differences:

- **Append; never rewrite.** Existing milestones, whatever their status, are
  history or in-flight work, and stay byte-for-byte as they are, archived ones
  included. Read their headings, outcomes and `### Architecture` fields for what
  already exists to build on; read an archived milestone only if a new one
  depends on its detail.
- **Number after the highest existing milestone**, ignoring split suffixes:
  after `M19j` and `M36` comes `M37`.
- **Map only the new ids** in `state.json`'s `requirements`, each to one new
  milestone, and add the new milestones to `state.json` at `TODO` with no plan.

The coverage gate applies to the new milestones and any architecture components
they advance; it does not reopen components earlier milestones exercised.

### Slice thin, end to end

A milestone is a **thin vertical slice**: the narrowest behaviour that runs
through the whole system, not one layer of it built out. The first slice is a
walking skeleton — the thinnest path that works end to end — and later slices
deepen it.

Every milestone must carry at least one acceptance criterion **exercised through
a real entry point**: a CLI invocation, an HTTP request, a public API call. If the
only way to demonstrate a milestone is a unit test of an internal component, it is
a component milestone and must be re-cut.

Order slices by integration risk, not by convenience. The first one should prove
the part most likely to be wrong, because that is the evidence worth having early.
A layered plan defers every integration risk to the end, where it costs the most
to act on.

**Thin is not a shortcut through the architecture.** The pressure a slice creates
is to bypass a boundary — to write persistence inline in the CLI because that is
the fastest route to something working. Do not. A slice crosses every boundary the
architecture defines; it crosses each one shallowly. A component may be a stub in
an early slice, but the seam is real from the first slice onwards, and dissolving
one silently is the defect this harness treats most seriously (see Architecture
in `${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md`).

When `.harness/architecture.md` exists, each milestone's `### Architecture` field
lists the component ids that slice **advances**. A slice normally advances several
components a little rather than completing any one, and a component is legitimately
built across several slices — partial, or stubbed behind a real seam, in the early
ones.

Before finishing generation, check the coverage gate: **every component must be
exercised by at least one milestone.** A component nothing exercises is either a
planning gap or a component that should not be in the architecture — resolve it
rather than leaving it unbuilt. The gate is about coverage, not about one
milestone per component; mapping them one-to-one produces a layered plan.

Milestones describe outcomes, not components: `M1 — Accounts can be created`, not
`M1 — Build C1`.

With no architecture file, write `N/A` in that field.

Good — each runs end to end and is demonstrable through the API:
```
M1 — An account can be created through the API and survives a restart
M2 — Duplicate emails are rejected with a clear error
M3 — Accounts can be listed and paged
```

Bad — layers. Nothing is demonstrable until the last one:
```
M1 — User domain model supports account creation
M2 — User creation API is exposed
M3 — User creation is integrated with persistence
```

Bad — implementation steps:
```
M1 — Create files
M2 — Add classes
M3 — Write functions
M4 — Write tests
```

### How big is a milestone

Size a milestone by its **acceptance criteria and operational complexity**.
Target **3-5** criteria, and past **7** it is two milestones. Also split when
reconnaissance shows any of these independent pressure signals:

- more than three affected subsystems;
- concurrency or lifecycle ownership changes;
- implementation combined with live-environment proof;
- more than roughly eight expected production files;
- more than six anticipated worker tasks; or
- multiple independently demonstrable outcomes.

One signal is a prompt to find a smaller seam; two signals require a split. A
concurrency/lifecycle change combined with live-environment proof also requires a
split even if it is the same outward outcome. Record the signal names in the
first child milestone's outcome. Decide this during generation, before writing
acceptance work or task packets — a milestone that is too large is otherwise not
discovered until it has already cost a long context to run.

Criteria are one reproducible measure because they are fixed here, visible in
`milestones.md` afterwards, and checkable by a human without watching the run.
They are not the sole measure: a short checklist can still hide several runtime
owners, failure modes and proof environments.

Split on the outcome, not the checklist: two milestones each of which is
independently implementable, testable and reviewable, not one outcome with its
criteria dealt out between them. If a split leaves a half that cannot be reviewed
on its own, the seam is in the wrong place.

Milestones should still be meaningful outcomes rather than microtasks — but
"a small number of milestones" is not itself a goal, and buying fewer milestones
by making each one larger costs far more than it saves.

## When you pick up a milestone: check its size and shape

The budget and the slice rule above are applied when milestones are *generated*.
A milestone you are picking up may have been planned before those rules existed,
or by a run that got them wrong. Check it now, before you break it into tasks —
the alternative is discovering it at turn 250, which is exactly what the budget
exists to prevent.

This is a **planning-phase** check, run on the first planning phase of a
milestone that has not started: `Status: TODO`, with no `Baseline` and an empty
`Evidence`. Never split a
milestone that is already `IN_PROGRESS` with work recorded against it, and never
during a review/fix cycle — the diff, the review and the criteria would no longer
describe the same thing. An oversized milestone discovered mid-flight is a
`Follow-ups` note, not a split.

Three checks, against the milestone you are about to run, before acceptance work
or task packets are created:

**Size.** Count its acceptance criteria.

```
1-5    run it
6-7    run it; note the size under Follow-ups
8+     split it before running anything
```

**Shape.** Does at least one acceptance criterion exercise the behaviour through
a real entry point — a CLI invocation, an HTTP request, a public API call? If the
only way to demonstrate the milestone is a unit test of an internal component, it
is a component milestone, and "Slice thin, end to end" above says it must be
re-cut. A milestone whose `Architecture` field names exactly one component is the
usual symptom, not the proof; read the criteria.

**Operational complexity.** From lightweight reconnaissance, count these named
signals:

- `SUBSYSTEMS_GT_3`: more than three affected subsystems;
- `CONCURRENCY_LIFECYCLE`: concurrency or lifecycle ownership changes;
- `IMPLEMENTATION_PLUS_LIVE_PROOF`: implementation and live-environment proof;
- `PRODUCTION_FILES_GT_8`: more than roughly eight expected production files;
- `WORKER_TASKS_GT_6`: more than six anticipated worker tasks;
- `MULTIPLE_OUTCOMES`: multiple independently demonstrable outcomes.

One signal requires an explicit seam check. Two or more require a split, as does
the combination of `CONCURRENCY_LIFECYCLE` and
`IMPLEMENTATION_PLUS_LIVE_PROOF`. A small coherent cross-file change with no
signal is not split merely because it touches several files. Record the signal
names in structured state and in the first child milestone's outcome.

### Splitting a milestone you did not plan

Split it in `.harness/state.json` and `.harness/milestones.md`, validate that the
two agree, then **return `SPLIT` without planning any part**. The
`plan` skill dispatches a fresh planning phase for the first part.
Splitting is cheap and planning a part costs a context of its own; do not spend
the context you just saved by carrying on into it.

Rules for the split:

- **Suffix, do not renumber.** `M6` becomes `M6a`, `M6b`, `M6c`. Renumbering
  every later milestone invalidates every reference to them — in the archive, in
  commit messages, in the architecture file, and in whatever the human remembers.
- **Conserve the criteria exactly.** Every acceptance criterion from the original
  appears in exactly one part, unchanged in wording. None added, none dropped,
  none reworded. Count them before and after and confirm the totals match.
- **Split on the outcome, not the checklist** — the rule in "How big is a
  milestone" applies unchanged. Each part must be independently implementable,
  testable and reviewable. If a part cannot be reviewed on its own, the seam is
  in the wrong place.
- **Each part gets every template heading**, an `### Outcome` of its own, and its
  own `### Architecture` field. Carry the original's `### Follow-ups` to the part
  they belong to.
- **Record that you split it, and why**, in the first part's `### Outcome` and
  structured state — one sentence naming the original milestone and every named
  criterion-count or operational-complexity signal that triggered it.
  A human reading the file later should not have to work out where `M6a` came
  from.
- Say in your return that you split rather than planned, and what the parts
  are.

A milestone that fails the **shape** check is a re-cut, not a split: its criteria
have to be reorganised into slices rather than dealt into piles, and that may
change their wording. That is a planning decision with no obviously correct
answer, so do not do it silently — set the milestone `BLOCKED`, record the
problem through the Human Escalation Contract in
`${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md` with a proposed re-cut, and let a
human agree it.

## Writing the task plan

The plan is what a human reads to agree the milestone before any of it runs. It
is written for them, not for you: what will be built, in what order, by which
tier and why, and what could go wrong — in plain words a busy person can judge
without opening the code.

**Plan against what will exist, not only what does.** The skill plans several
milestones in a row before any of them runs, so the one in front of you may
build on milestones that are planned but not yet built. Read their plans (and
only the packets your tasks depend on) for the names, files and interfaces
they will produce, and write your packets against those. Say in the plan's
`## Risks and open points` which tasks rest on an earlier milestone's planned
work, so the human sees the dependency.

After the size and shape check passes:

1. Break the milestone into tasks — normally 3-6; more than six is the
   `WORKER_TASKS_GT_6` signal and should have been caught above. Each task is
   independently verifiable and names the acceptance criteria it advances.
   Every criterion is advanced by at least one task.
2. Route each task by the Routing rule in
   `${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md`, now rather than at dispatch:
   the tier and its reason are part of what the human agrees.
3. Write each task packet to `.harness/tasks/<milestone>-<task>.md`, and record
   each task in `.harness/state.json` with its `id`, `scope`, `routing` and
   `artifact` (the packet path).
4. Write `.harness/plans/<milestone>.md` using exactly
   `${CLAUDE_PLUGIN_ROOT}/skills/plan/references/plan-template.md`,
   at `Status: DRAFT`. Set the milestone's `plan` in structured state to
   `{"status": "DRAFT", "artifact": ".harness/plans/<milestone>.md"}` and its
   `### Plan` field in `milestones.md` to `<that path> — DRAFT`.
5. Run `check-state.py`, commit the explicit `.harness/` paths as
   `M<n>: task plan (draft)` on the current branch — the skill has put you on
   a plans branch; open no other — and return `PLANNED` with the plan path.

**A revision** arrives with the plan path and the human's requested changes,
verbatim. Apply them to the plan, the packets and structured state together, so
the three never describe different work; record nothing under `## Changes during
implementation`, which is for after agreement. If a requested change would split
the milestone, split it as above and return `SPLIT`; the skill plans the parts.
If a revision changes a name, file or interface that a later milestone's DRAFT
plan relies on, say which in your return, so the skill can have that plan
revised too. If a request contradicts a requirement or
acceptance criterion, do not apply it — say so in your return, so the human can
change the requirement through `roast-requirements` instead.

**Never set the plan to `AGREED`.** Only a human agrees a plan, through the
`plan` skill.
