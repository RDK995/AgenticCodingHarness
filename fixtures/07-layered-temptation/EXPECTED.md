# 07 — Layered temptation

First validated in **B22**. The only fixture that tests **planning**; 01-06 all
test review or execution.

## What this fixture discriminates

Whether milestone generation produces **thin end-to-end slices** or **one milestone
per component**, given an architecture whose components divide cleanly by tier —
HTTP, service, store, clock, config. That division is honest: it is how the
responsibilities actually split. It is also exactly the shape that invites a build
order of config → clock → store → service → API, in which nothing is demonstrable
until the last milestone.

## Setup

Agreed requirements and an `AGREED` architecture. **No `milestones.md`** — the
harness generates it, and that generation is the thing under test. No source.

The trap is deliberately symmetrical: there are **5 components and 5 acceptance
criteria**. A layered plan and a sliced plan can both produce five milestones, so
milestone *count* discriminates nothing. What separates them is which components
each milestone touches.

```bash
git init -q && git add -A && git commit -qm baseline
```

## Command

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Bash Grep Glob Task Agent" \
  --agent harness:orchestrator \
  -p "Generate milestones for this project. Planning only — implement nothing."
```

## Expected outcome

**Mechanically checkable, and independent of this fixture's domain:**

- `.harness/milestones.md` exists and every milestone carries the template
  headings in order.
- No milestone has more than **5** acceptance criteria.
- **Every milestone's `### Architecture` field names at least 2 components.** A
  slice crosses boundaries; a layer sits inside one.
- **No milestone names exactly one component.** That is the layered signature.
- **C1 and C2 each appear in at least 3 milestones.** Every behaviour in this
  system is served through the API and decided by the service, so under slicing
  they recur; under layering each appears once.
- Every milestone has at least one acceptance criterion naming an HTTP method and
  path (`POST /links`, `GET /{code}`, `GET /links/{code}/stats`).
- Every one of C1-C5 is exercised by at least one milestone.

**Requires reading the report:**

- The first milestone is a walking skeleton — a URL can be shortened and the short
  link followed, end to end — not a foundation, a schema, or a config loader.
- No milestone is named after a component or a layer.
- Criteria assert **observable** behaviour: status codes, `Location` headers,
  response bodies. Not "the store exposes `save()`", not "the service returns a
  `Link`", not the table's schema.
- No single criterion carries a subsystem. "Creates the row, generates the code,
  builds the short URL, and returns 201" is four assertions and a milestone in
  disguise.
- Ordering is justified by integration risk, not by dependency convenience.

## Failure modes worth recognising

- **One milestone per component** — `M1 — Config`, `M2 — Clock`, `M3 — Store`,
  `M4 — Link service`, `M5 — HTTP API`. The default failure, and the most
  tempting here because the counts line up: five components, five criteria, five
  milestones. It will look tidy and complete, and nothing is demonstrable until M5.
- A "foundations", "scaffolding", or "data model" milestone. A milestone that
  builds no behaviour is a layer whatever it is called.
- Slices that pass the letter of the entry-point rule while asserting internal
  structure — driving `POST /links` and then asserting the row shape rather than
  the response.
- Splitting by HTTP verb rather than by behaviour: `M1 — all POST endpoints`,
  `M2 — all GET endpoints` is still layering.
