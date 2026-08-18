---
name: roast-requirements
description: Converts rough, ambiguous requirements into agreed, implementation-ready requirements by probing for material ambiguity before writing .harness/requirements.md. Use when the user gives a rough feature/bug description and wants it turned into requirements, or explicitly asks to "roast" requirements.
---

Turn the user's rough input into agreed, implementation-ready requirements written to
`.harness/requirements.md`. Do not begin implementation work from this skill — its only
output is an agreed requirements document.

Use the template at [references/requirements-template.md](references/requirements-template.md)
for the exact file structure to write.

## Step 1 — Read the input

Read the user's rough requirement as given (in the conversation, or an existing
`.harness/requirements.md` if one is being revised).

## Step 2 — Look for gaps

Scan for:

- ambiguity
- contradictions
- unstated assumptions
- unclear system boundaries
- missing failure behaviour
- missing edge cases
- unclear integrations
- missing acceptance criteria
- unnecessary complexity
- security-sensitive behaviour
- material performance constraints

## Step 3 — Ask only what matters

Ask only questions whose answers could materially affect the implementation.
Prefer grouped questions over one-at-a-time.

Do not ask implementation-detail questions Claude can reasonably decide later
(naming, internal data structure choice, private helper structure, etc.).

**Examples that should block / must be asked:**
- Should deleting an account permanently remove data?
- Who is authorised to perform this action?
- Does duplicate submission return the existing resource or an error?

**Examples that normally should NOT block / must not be asked:**
- What should this internal helper function be called?
- Should this private implementation use a map or array?

## Step 4 — Repeat until resolved

Keep asking (in as few rounds as possible) until:

> No unresolved question is likely to materially change the implementation.

## Step 5 — Confirm with the human

Present the interpreted requirements back to the human in full. Require explicit
agreement before treating requirements as complete. If the human pushes back or
introduces new information, return to Step 2.

## Step 6 — Write the file

Write `.harness/requirements.md` using the template. Set:

```
## Open Questions

None
```

only once the requirements gate below has passed. If material ambiguity remains
(the human hasn't confirmed, or a blocking question is unanswered), list the
open questions there instead and do not claim the gate has passed.

## Requirements Gate

Downstream implementation work (the `implement` skill / orchestrator) must not start while:

```
Open Questions != None
```

or while Claude believes a material ambiguity remains, even if not yet written down.
Minor technical decisions the human wasn't asked about do not block this gate.
