# Planning a milestone

Read this on an **implementation phase**, before you break anything into tasks.
A fix cycle never needs it: the milestones exist by then, and the one in front of
it has already been picked up and sized.

Reconnaissance and the size/shape check run every implementation phase.
"Generating milestones" runs once per project — only when
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
itself. The file holds milestones only.

Milestones represent **observable outcomes**, not implementation steps. Tests
belong inside each milestone, not as a separate milestone.

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

Size a milestone by its **acceptance criteria**: target **3-5**, and past **7**
it is two milestones. Decide that here, during generation — a milestone that is
too large is not discovered until it has already cost a long context to run.

Criteria are the measure because they are fixed here, visible in
`milestones.md` afterwards, and checkable by a human without watching the run.
Each one needs an implementation, a test, and recorded evidence, so ten criteria
is not a large milestone — it is two or three milestones that were written as
one.

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

This is an **implementation-phase** check, and only on a milestone that has not
started: `Status: TODO`, with no `Baseline` and an empty `Evidence`. Never split a
milestone that is already `IN_PROGRESS` with work recorded against it, and never
during a review/fix cycle — the diff, the review and the criteria would no longer
describe the same thing. An oversized milestone discovered mid-flight is a
`Follow-ups` note, not a split.

Two checks, against the milestone you are about to run:

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

### Splitting a milestone you did not plan

Split it in `.harness/milestones.md`, then **return without implementing
anything**. The skill re-enters its loop and a fresh context runs the first part.
Splitting is cheap and implementing is not; do not spend the context you just
saved by carrying on into the work.

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
- **Record that you split it, and why**, in the first part's `### Outcome` —
  one sentence naming the original milestone and the count that triggered it.
  A human reading the file later should not have to work out where `M6a` came
  from.
- Say in your return that you split rather than implemented, and what the parts
  are.

A milestone that fails the **shape** check is a re-cut, not a split: its criteria
have to be reorganised into slices rather than dealt into piles, and that may
change their wording. That is a planning decision with no obviously correct
answer, so do not do it silently — set the milestone `BLOCKED`, record the
problem through the Human Escalation Contract in
`${CLAUDE_PLUGIN_ROOT}/agents/orchestrator.md` with a proposed re-cut, and let a
human agree it.
