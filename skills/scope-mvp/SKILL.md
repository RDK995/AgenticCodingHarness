---
name: scope-mvp
description: Carves an agreed full-scope requirements document and architecture into an MVP that proves the project's riskiest assumption, plus an ordered expansion path back to full scope. Writes the MVP to .harness/requirements.md and .harness/architecture.md so implement runs against it unchanged, preserving the full documents under .harness/full/. Use after roast-requirements (and architect) when a concept should be proven before the system is built out.
---

Turn an agreed full scope into an MVP that can be implemented, judged, and then
expanded. Do not implement anything from this skill — its outputs are three
documents: an MVP-scoped `.harness/requirements.md`, an MVP-scoped
`.harness/architecture.md`, and `.harness/mvp.md`, the record of what was cut and
in what order it comes back.

Use the template at [references/mvp-template.md](references/mvp-template.md) for
`.harness/mvp.md`. The other two files keep their existing templates —
`roast-requirements/references/requirements-template.md` and
`architect/references/architecture-template.md` — because everything downstream
already reads those two paths, and the MVP has to be the thing the harness
implements, not a fourth document beside it.

## When this skill applies

When the full scope is agreed and something in it is genuinely uncertain: the
approach might not work, the users might not want it, the integration might not
behave, the performance might not be there. The MVP exists to find that out for
the least work.

It does not apply when:

- **Nothing is uncertain.** The harness already builds thin end-to-end slices in
  risk order. An MVP that proves nothing is just the first slice with a ceremony
  around it. Say so and send the user to `implement`.
- **The work is small.** If the full scope is a handful of milestones, carving it
  costs more than building it.
- **The project is already mid-build.** See the gate.

## Gate — do not start without an agreed full scope

```
Read .harness/requirements.md
IF missing:            tell the user to run roast-requirements first; STOP
IF Open Questions != None:  STOP and quote the unresolved questions back

Read .harness/architecture.md, if present
IF Status != AGREED:   STOP — tell the user to finish the architect skill

Read .harness/mvp.md, if present
IF Status == AGREED:   this project is already carved — go to "Expanding later"

Read .harness/milestones.md, if present
IF any milestone is not TODO:
    STOP — the project is mid-build. Re-scoping now would orphan the evidence
    already recorded against milestones planned for a different scope. Tell the
    human what has been built and let them decide.
```

An MVP carved from ambiguous requirements proves the wrong thing precisely and
convincingly. The gate is the same one the architect enforces, for the same
reason: scope decisions inherit whatever ambiguity is upstream of them.

## Step 1 — Name what the MVP proves

Write one sentence, in a form that can turn out to be false:

```
Riskiest assumption: <the thing that, if untrue, changes or kills the project>
Kind: technical | product | integration | performance
```

Choose the assumption whose failure is most expensive to discover late, not the
one that is most interesting to build. Then every later decision in this skill is
derived rather than a matter of taste: in scope means *the proof needs it*.

If you cannot name an assumption that could plausibly be false, stop and say so.
The honest recommendation is then to skip the MVP phase.

## Step 2 — Carve the requirements

Every entry under `## Functional Requirements` is either **IN** or **DEFERRED**.
There is no third state, and each `IN` carries a one-line reason tied to the
assumption in Step 1.

**In scope:**

- One complete path end to end, crossing every boundary the assumption touches —
  shallowly, but crossing each one. A vertical slice, not a layer.
- Whatever makes the result legible to the human who has to judge it. A proof
  nobody can read is not a proof.

**Deferred:**

- Breadth — the second and third variant of a shape the first one already proves.
- Scale, operational polish, admin surfaces, migration and backfill,
  configuration options.
- Authentication, authorisation and multi-tenancy, *unless* the assumption is
  about them.
- Error handling beyond failing loudly and visibly.

**Never deferred, however much smaller it would make the MVP:** correctness of
what is in scope, tests, and the evidence trail. Cut features, not engineering.
An MVP you cannot trust proves nothing, and the harness's completion gate will
refuse it anyway.

`## Constraints` and `## Non-Goals` carry across unchanged unless the human
explicitly agrees to relax one. A constraint quietly dropped is how an MVP comes
to prove a concept the real system is not allowed to have.

Then check the cut for a hidden dependency: an in-scope requirement whose path
silently runs through something you deferred. That is the failure mode of this
step, and it surfaces during implementation as an unplanned expansion.

## Step 3 — Carve the architecture

Skip this step if the project has no `.harness/architecture.md` — carve the
requirements only, and record `Architecture: None — existing codebase` in
`.harness/mvp.md`.

Each component from the full architecture gets one of three treatments:

- **IN** — built for real, though only as deep as the slice needs.
- **STUBBED** — the boundary exists, the implementation behind it is trivial.
  Allowed only when the slice cannot run without something there *and* the real
  implementation later slots in behind the same interface unchanged.
- **DEFERRED** — absent from the MVP entirely, along with the requirements that
  needed it.

Component ids are stable. Reuse the full architecture's `C1…Cn` exactly; never
renumber, and never reuse a deferred component's id for something else. The ids
are the link between the MVP, the full scope, and every milestone written against
either.

Two rules pull against each other here, and both hold:

- **Do not build for what you deferred.** No extension points, no abstraction
  without a current use, no configuration for a variant nobody has asked to run.
- **Do not dissolve a boundary because the MVP would be shorter without it.**
  Inlining persistence into the CLI produces a working proof of a system nobody
  can expand — and it is the exact drift the reviewer exists to catch.

Then take the **structural commitments** at full-scope fidelity even where the
MVP would not notice: identity and ownership keys in the data model, whether an
operation is synchronous or queued, where the trust boundary sits, what the unit
of concurrency is. These are cheap now and expensive once a proven system rests
on them. This is not designing for hypothetical requirements — it is choosing the
shape of what you are building today so that the proof survives being expanded.
Record them, with the reason.

Finally redraw `## Diagram` for the MVP components only, marking stubs, and cut
`## Requirement Coverage` down to the in-scope requirements. The template's rule
still applies: the diagram renders the text, so if drawing it makes you want to
change the carve, change the carve and redraw.

## Step 4 — State the proof, and what would falsify it

Write the MVP's acceptance criteria so that at least one is demonstrable through
the system's real entry point — a CLI invocation, an HTTP request, a public API
call — not solely a unit test of internals. The same demonstrability rule the
milestones follow.

Then write, before anything is built, the result that would mean the concept is
**not** proven. An MVP with no falsifying outcome always succeeds, and the
expansion is then committed to on no evidence at all.

## Step 5 — Order the expansion

Turn the deferred set into increments `E1…En`, ordered by dependency first and
then by what the MVP's result would most change. For each: what it adds (by
reference to the full documents) and what the MVP must not have precluded.

This is an order, not a plan. Milestones are planned by the harness when an
increment is actually promoted, against the scope as it is then.

## Step 6 — Present and require agreement

Present the carve in full and require explicit agreement. Lead with the
assumption and the cut list — what is *missing* is where the human will disagree,
and it is cheaper to disagree now than after the proof is built.

Cover: the assumption and its falsifier, what is in scope and why the proof needs
it, everything deferred and why deferring is safe, the MVP diagram, the
structural commitments, and the expansion order.

If the human changes what the system must ultimately do, send them back to
`roast-requirements`; if they change the full design, back to `architect`.
Requirements and architecture are upstream of scoping, and editing them here
bypasses their gates.

## Step 7 — Write the files

Only after explicit agreement:

```
1. Move the full documents aside, unchanged:
       .harness/requirements.md   -> .harness/full/requirements.md
       .harness/architecture.md   -> .harness/full/architecture.md   (if present)
       .harness/milestones.md     -> .harness/full/milestones.md     (if present,
                                     all TODO — they were planned for a scope
                                     that is no longer the one being built)

2. Write .harness/requirements.md — the MVP scope, using the requirements
   template. Goal narrowed to the assumption being proven; in-scope functional
   requirements; the Step 4 acceptance criteria; constraints carried across;
   every deferred reference listed under ## Non-Goals with a pointer to
   .harness/mvp.md; Open Questions: None.

3. Write .harness/architecture.md — the MVP architecture, using the architecture
   template, Status: AGREED. (Skip if the project has none.)

4. Write .harness/mvp.md from references/mvp-template.md, Status: AGREED.
```

Move the full documents; never edit them in place. They are what the expansion is
measured against, and a full scope that has been quietly trimmed to match the MVP
cannot serve that purpose.

Then tell the human to `/clear` and run `/harness:implement`, which will plan
milestones against the MVP scope with no knowledge that it is one — which is the
point.

## Expanding later

Once the MVP is `DONE` and the final review has passed, the human judges the
result against the falsifier from Step 4.

**Proven.** Re-invoke this skill. It reads `.harness/mvp.md`, takes the next
increment, folds that increment's requirements and components back from
`.harness/full/` into `.harness/requirements.md` and `.harness/architecture.md`,
and records the promotion under `## Decisions` with the date and the evidence the
proof rested on. Hand back to `implement`, which plans new milestones for the
added scope. Milestones already `DONE` stay `DONE` and are not re-planned.

**Falsified.** The answer is not a larger MVP. Take what was learned back to
`roast-requirements`; the requirements are what changed.

Either way, read `.harness/as-built/drift.md` if the project has one before
promoting anything. It is the evidence for whether the MVP actually built the
boundaries the expansion assumes it can build on, as opposed to the ones it
claimed.

## Never

- Never write code, scaffolding, or directory structure from this skill. A scope
  decision is not an implementation.
- Never mark `Status: AGREED` because the carve looks reasonable to you. Deciding
  what to leave out of a product is not a decision you get to both make and
  certify.
- Never edit or delete the full documents. They move once, and are read
  thereafter.
- Never defer tests, correctness of in-scope behaviour, or evidence in order to
  make the MVP smaller. Smaller, not sloppier.
- Never build anything for a deferred increment. Structural commitments are the
  shape of what you build now, not code for what comes later.
- Never leave the MVP without a result that would falsify it.
- Never let the MVP's `requirements.md` hide what was cut. Every deferred
  reference is named in `## Non-Goals`, so a session that only ever sees the MVP
  can still tell that a full scope exists and where it lives.
