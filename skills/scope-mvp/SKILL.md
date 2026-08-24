---
name: scope-mvp
description: Carves an agreed full-scope requirements document and architecture down to the smallest implementation that delivers end-to-end value on its own, plus an ordered expansion path back to full scope. Asks the human whatever it needs to make the cut. Writes the MVP to .harness/requirements.md and .harness/architecture.md so implement runs against it unchanged, preserving the full documents under .harness/full/. Use after roast-requirements (and architect) when the full scope is larger than the first thing worth having.
---

Turn an agreed full scope into the smallest implementation that is worth using on
its own, and record the order the rest comes back in. Do not implement anything
from this skill — its outputs are three documents: an MVP-scoped
`.harness/requirements.md`, an MVP-scoped `.harness/architecture.md`, and
`.harness/mvp.md`, the record of what was cut and when it returns.

Use the template at [references/mvp-template.md](references/mvp-template.md) for
`.harness/mvp.md`. The other two files keep their existing templates —
`roast-requirements/references/requirements-template.md` and
`architect/references/architecture-template.md` — because everything downstream
already reads those two paths, and the MVP has to be the thing the harness
implements, not a fourth document beside it.

## What an MVP is here

The smallest implementation that carries one real user from the system's entry
point to a result they actually wanted, with nothing in between left as a promise.

Two halves, and both are load-bearing:

- **End to end.** The path runs through the system's real entry point to a real
  result. Not a layer, not a component, not a demo that stops one step short of
  the thing the user came for.
- **Valuable.** Someone would use it even if nothing more were ever built. If the
  honest answer to "would anyone use this?" is no, what has been scoped is a
  prototype, and calling it an MVP hides the fact that the value is still ahead.

Smallest is the constraint applied to those two, not a third goal that can
override them. Cutting until the path no longer reaches a result produces
something smaller than an MVP and less useful than either half.

## When this skill applies

When the full scope contains a path that is worth having well before all of it is
built. That is most projects.

It does not apply when:

- **The full scope is already minimal.** If nothing can come out without breaking
  the path to a result, say so and send the user to `implement`.
- **Nothing short of the whole thing is usable.** Some scopes are all-or-nothing
  for regulatory, contractual or integration reasons. Name the reason and stop
  rather than carving a version that cannot be released.
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

An MVP carved from ambiguous requirements ships the wrong thing quickly. The gate
is the same one the architect enforces, for the same reason: scope decisions
inherit whatever ambiguity is upstream of them.

## Step 1 — Name the outcome the MVP delivers

Write one sentence:

```
A <specific user> can <complete outcome> through <the real entry point>.
```

Then name what that replaces — what the user does today, or does without — so the
value is stated as a change in their situation rather than as a feature list.

If the full scope serves several users or several outcomes, exactly one of them is
the MVP. Choosing is the work of this skill; serving all of them thinly is how an
MVP ends up being neither small nor usable.

Everything after this step is derived rather than negotiated: in scope means *the
outcome cannot be completed without it*.

## Step 2 — Ask the human what you cannot decide

The cut is often not derivable from the documents alone. Ask, in as few rounds as
possible, grouped rather than one at a time. Ask only questions whose answer moves
something between in scope and deferred.

**Ask when unresolved:**

- Which user or scenario comes first, if the requirements serve several?
- What is the one outcome that would make this worth using on its own?
- Who uses the MVP — real users, or the team? This sets the floor for
  authentication, data handling and error behaviour, and it is the answer most
  likely to move several requirements at once.
- Does it run against real data and real systems, or is sample data enough for the
  first version?
- Where is a manual step acceptable — something a person does that the full scope
  automates — and where would that make the result not worth using?
- How much of the full scope's breadth is needed before the outcome is real: one
  case, one integration, one format, or more?
- Is anything non-negotiable even in a first version — legal, safety, contractual,
  or a constraint someone has already promised?

**Do not ask** what you can decide and record: internal naming, private data
structures, library versions, test style, module layout.

If an answer changes what the system must ultimately *do*, that is a requirements
change: send the human to `roast-requirements` rather than absorbing it here.

Record the answers under `## Decisions` in `.harness/mvp.md` so the next session
does not re-ask them.

## Step 3 — Carve the requirements

Every entry under `## Functional Requirements` is either **IN** or **DEFERRED**.
There is no third state, and each `IN` carries a one-line reason tied to the
outcome from Step 1.

**In scope:**

- Every step on the path from the entry point to the result. A missing step in the
  middle is not a smaller MVP, it is a broken one.
- Whatever the result needs to be *usable* rather than merely demonstrable — if
  the outcome depends on the work surviving until tomorrow, then persistence is on
  the path, however much smaller it would be without it.

**Deferred:**

- Every path that is not the one. Alternate flows, second and third variants,
  additional formats, additional integrations.
- Breadth of case coverage beyond what makes the one outcome real.
- Scale, operational polish, admin surfaces, migration and backfill,
  configuration options.
- Authentication, authorisation and multi-tenancy — *unless* Step 2 established
  that the MVP goes to real users or touches data that requires them.
- Error handling beyond failing loudly and visibly.

**Manual steps are allowed and must be named.** Where a person does something the
full scope automates, record it under `## Manual Steps` in `.harness/mvp.md` and
put the automation in the deferred set. A manual step that is written down is a
scope decision; an unwritten one is a gap that surfaces the first time someone
uses the system.

**Never deferred, however much smaller it would make the MVP:** correctness of
what is in scope, tests, and the evidence trail. Cut scope, not engineering. The
completion gate will refuse the milestone anyway, and shipping something nobody
can trust to a real user is worse than shipping later.

`## Constraints` and `## Non-Goals` carry across unchanged unless the human
explicitly agrees to relax one. A constraint quietly dropped is how an MVP comes
to deliver value the real system is not allowed to deliver.

Then check the cut for a hidden dependency: an in-scope step whose path silently
runs through something you deferred. That is the failure mode of this step, and it
surfaces during implementation as an unplanned expansion.

## Step 4 — Carve the architecture

Skip this step if the project has no `.harness/architecture.md` — carve the
requirements only, and record `Architecture: None — existing codebase` in
`.harness/mvp.md`.

Each component from the full architecture gets one of three treatments:

- **IN** — built for real, though only as deep as the path needs.
- **STUBBED** — the boundary exists, the implementation behind it is trivial.
  Allowed only when the path cannot run without something there *and* the real
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
  Inlining persistence into the CLI produces something that works and cannot be
  grown — and it is the exact drift the reviewer exists to catch.

Then take the **structural commitments** at full-scope fidelity even where the MVP
would not notice: identity and ownership keys in the data model, whether an
operation is synchronous or queued, where the trust boundary sits, what the unit
of concurrency is. These are cheap now and expensive once real users and real data
rest on them. This is not designing for hypothetical requirements — it is choosing
the shape of what you are building today so the first version can be grown rather
than replaced. Record them, with the reason.

Finally redraw `## Diagram` for the MVP components only, marking stubs, and cut
`## Requirement Coverage` down to the in-scope requirements. The template's rule
still applies: the diagram renders the text, so if drawing it makes you want to
change the carve, change the carve and redraw.

## Step 5 — Say what "delivered" means

Write the MVP's acceptance criteria so that at least one walks the **whole path**
through the system's real entry point — a CLI invocation, an HTTP request, a
public API call — and ends at the result the user came for. The same
demonstrability rule the milestones follow, applied to the outcome rather than to
a component.

Then write the line that keeps the MVP honest:

```
Not delivered if: <a result that leaves the user still doing what the MVP was
                   meant to replace>
```

Written before the build, that line is what makes "the tests pass" and "the
outcome is delivered" different claims. An MVP with only the first one can be
complete and useless at the same time.

## Step 6 — Order the expansion

Turn the deferred set into increments `E1…En`, ordered by dependency first and
then by what the first users will miss soonest — the manual step that becomes
tiring, the second case that turns up immediately, the breadth that arrives with
the second user.

For each: what it adds (by reference to the full documents) and what the MVP must
not have precluded.

This is an order, not a plan. Milestones are planned by the harness when an
increment is actually promoted, against the scope as it is then.

## Step 7 — Present and require agreement

Present the carve in full and require explicit agreement. Lead with the
one-sentence outcome and the cut list — what is *missing* is where the human will
disagree, and it is cheaper to disagree now than after it is built.

Cover: the outcome and what it replaces, what is in scope and why the outcome
needs it, everything deferred and why deferring is safe, any manual steps, the
MVP diagram, the structural commitments, and the expansion order.

If the human changes what the system must ultimately do, send them back to
`roast-requirements`; if they change the full design, back to `architect`.
Requirements and architecture are upstream of scoping, and editing them here
bypasses their gates.

## Step 8 — Write the files

Only after explicit agreement:

```
1. Move the full documents aside, unchanged:
       .harness/requirements.md   -> .harness/full/requirements.md
       .harness/architecture.md   -> .harness/full/architecture.md   (if present)
       .harness/milestones.md     -> .harness/full/milestones.md     (if present,
                                     all TODO — they were planned for a scope
                                     that is no longer the one being built)

2. Write .harness/requirements.md — the MVP scope, using the requirements
   template. Goal narrowed to the outcome from Step 1; in-scope functional
   requirements; the Step 5 acceptance criteria; constraints carried across;
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

Once the MVP is `DONE`, the final review has passed, and someone has actually used
it, re-invoke this skill. It reads `.harness/mvp.md`, takes the next increment,
folds that increment's requirements and components back from `.harness/full/` into
`.harness/requirements.md` and `.harness/architecture.md`, and records the
promotion under `## Decisions` with the date and what prompted it. Hand back to
`implement`, which plans new milestones for the added scope. Milestones already
`DONE` stay `DONE` and are not re-planned.

Two things are worth checking before promoting anything.

**Use, not assumption, should pick the increment.** The expansion order was
written before anyone had the system. If the first users needed something else,
reorder `## Expansion Path` and record why — that is the whole reason to build the
small version first.

**Read `.harness/as-built/drift.md` if the project has one.** It is the evidence
for whether the MVP actually built the boundaries the expansion assumes it can
build on, as opposed to the ones it claimed.

If the MVP turned out not to deliver its outcome, the answer is not the next
increment. Take what was learned back to `roast-requirements`; the requirements
are what changed.

## Never

- Never write code, scaffolding, or directory structure from this skill. A scope
  decision is not an implementation.
- Never mark `Status: AGREED` because the carve looks reasonable to you. Deciding
  what a product can ship without is not a decision you get to both make and
  certify.
- Never cut the path short of the result to make the MVP smaller. A path that
  stops before the outcome is not a minimum viable product, and calling it one
  moves the discovery that it is unusable to after it is built.
- Never edit or delete the full documents. They move once, and are read
  thereafter.
- Never defer tests, correctness of in-scope behaviour, or evidence in order to
  make the MVP smaller. Smaller, not sloppier.
- Never leave a manual step unrecorded. In the MVP it is a decision; undocumented
  it is a hole.
- Never build anything for a deferred increment. Structural commitments are the
  shape of what you build now, not code for what comes later.
- Never let the MVP's `requirements.md` hide what was cut. Every deferred
  reference is named in `## Non-Goals`, so a session that only ever sees the MVP
  can still tell that a full scope exists and where it lives.
