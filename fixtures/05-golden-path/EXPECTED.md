# 05 — Golden path

First validated in **B8**, re-run in **B14**. The baseline: does the workflow work
at all, end to end, with nothing deliberately broken?

## Setup

Agreed requirements only — no `milestones.md`, no `architecture.md`, no source.
The harness plans, implements, reviews and records from a standing start.

Also serves as the no-architecture regression: `architecture.md` is absent, so V1
behaviour applies and nothing should demand one.

```bash
git init -q && git add -A && git commit -qm baseline
```

## Command

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Bash Grep Glob Task Agent" \
  -p "/harness:implement"
```

## Expected outcome

**Mechanically checkable:**

- `.harness/milestones.md` exists, milestone reaches `Status: DONE`.
- Its headings match `skills/implement/references/milestones-template.md` exactly
  and in order.
- `### Architecture` is `N/A` — present, not omitted.
- The test suite passes when re-run independently, outside the agent's session.
- `divide(1, 0)` raises rather than returning a sentinel.

**Requires reading the report:**

- Every acceptance criterion carries both implementation and test evidence.
- A fresh review ran and its verdict is recorded.
- The final holistic review reports `COMPLETE`.

## Failure modes worth recognising

- Reporting success while `milestones.md` is still `TODO`, or while `Evidence` and
  `Validation` are empty — a claim without the evidence the gate requires.
- Demanding an `architecture.md` that this fixture deliberately does not have.
- Implementing the non-goals (add/subtract/multiply). They are stated as out of
  scope and belong in `### Follow-ups` if raised at all.
