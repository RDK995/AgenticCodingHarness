---
name: architect
description: Turns agreed requirements into an agreed architecture for a new project — proposes components, boundaries and technology choices, probes only materially-ambiguous design decisions, and writes .harness/architecture.md once the human agrees. Use after roast-requirements and before implement, when starting a new project rather than extending an existing codebase.
---

Turn `.harness/requirements.md` into an agreed architecture written to
`.harness/architecture.md`. Do not implement anything from this skill — its only
output is an agreed architecture document.

Use the template at [references/architecture-template.md](references/architecture-template.md)
for the exact file structure to write.

## When this skill applies

For a **new** project, where the architecture must be *decided*.

For an existing codebase the architecture is *discovered*, not decided — the
orchestrator's repository reconnaissance already does that, and duplicating it
here would be redundant. If the repository already has substantial source code,
say so and stop rather than inventing a parallel architecture for code that
already has one.

## Gate — do not start without agreed requirements

Read `.harness/requirements.md` first.

```
IF missing:
    tell the user to run the roast-requirements skill first
    STOP

IF Open Questions != None:
    STOP and quote the unresolved questions back
```

Architecture derived from ambiguous requirements bakes the ambiguity into the
structure of the system, where it is far more expensive to remove later.

## Step 1 — Propose the smallest architecture that satisfies the requirements

Design for what `requirements.md` actually asks for, including its `Constraints`
and `Non-Goals`. Do not add layers, abstractions, or extension points for
requirements nobody has stated — the same rule the implementation follows
(`Do not introduce abstractions without a current use`) governs the architecture
that precedes it.

Determine:

```
Components and their single responsibilities
Boundaries and interfaces between them
Key data shapes and where they live
Technology choices, and what you rejected
Material risks
```

Give each component an identifier `C1`, `C2`, … so milestones can reference it.

Then draw it. `## Diagram` is a Mermaid `flowchart` with one node per component
and one edge per `Depends on`, each edge labelled with what crosses that
boundary. Derive it from what you just determined rather than composing it
separately — it is the same information in the form that answers "what talks to
what" without the reader reconstructing the graph from four sections of prose.

If the graph is hard to draw, that is a result. Components with edges to
everything, or a cycle you did not intend, are visible in a diagram and nearly
invisible in a list.

## Step 2 — Ask only what is materially ambiguous

Ask only questions whose answer changes the structure of the system, and prefer
grouped questions over one at a time.

**Examples that should be asked:**
- Is this one deployable unit or several?
- Does this need durable storage, and must it survive restart?
- Is this interaction synchronous, or queued and eventually consistent?
- Which component owns authorisation decisions?

**Examples that should NOT be asked** — decide these yourself and record them:
- Internal module or file naming.
- Private data structure choices inside a component.
- Which test-assertion style to use.

If the requirements already answer a question, do not re-ask it; cite the
requirement instead.

## Step 3 — Check requirement coverage

Every entry under `## Functional Requirements` must map to at least one
component. A requirement with nowhere to live means the architecture is
incomplete — resolve it before presenting, not after.

## Step 4 — Present and require agreement

Present the proposed architecture to the human in full, **including the
diagram**, and including what you rejected and why. Require explicit agreement.

The diagram is the part most likely to draw a real objection — a boundary that
reads as reasonable in a sentence often reads as obviously wrong as an arrow — so
present it first and let the prose support it.

If the human pushes back or introduces new information, return to Step 1. If
their answer changes what the system must *do* rather than how it is built,
send them back to `roast-requirements` — requirements are upstream of
architecture, and editing them here would bypass the requirements gate.

## Step 5 — Write the file

Write `.harness/architecture.md` using the template, with:

```
## Status

AGREED
```

Set `AGREED` only after explicit human agreement. Until then write `DRAFT` and
list what is unresolved under `## Open Architecture Questions`. The implement
skill treats a `DRAFT` architecture the same way it treats unresolved
requirements: it stops.

## Never

- Never write code, scaffolding, or directory structure from this skill. An
  architecture document is not an implementation.
- Never mark an architecture `AGREED` because it looks reasonable to you. The
  point of the human gate is that you do not get to both choose the
  architecture and certify it.
- Never let the diagram and the text disagree. The diagram renders
  `## Components` and `## Interfaces`; if drawing it makes you want to change the
  design, change the design and redraw, rather than drawing what you wish were
  true.
- Never design for hypothetical future requirements. If you think one is coming,
  note it under `## Deviations` as a possibility, do not build for it.
