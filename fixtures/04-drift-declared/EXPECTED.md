# 04 — Declared deviation

First validated in **B13** (T6). Run it **with** `03`; alone it proves little.

## Setup

The same structural departure as `03` — C2 no longer exists as a separate
component and C1 owns persistence — with two differences:

1. The departure is honest. `note/store.py` is gone rather than left as dead code.
2. It is **recorded**, as `D1` under `## Deviations` in `architecture.md`, with what
   changed, why, and `Material: yes` plus human confirmation.

All four tests pass.

```bash
git init -q && git add -A && git commit -qm baseline
```

## Command

Same as `03`, against this directory.

## Expected outcome

**Mechanically checkable:**

- **No** architectural drift finding.
- Both acceptance criteria `PASS`.

**Requires reading the report:**

- The reviewer noticed the departure from the agreed components, checked
  `## Deviations`, found `D1`, and treated it as a decision rather than a defect.
- Its reasoning distinguishes declared from undeclared deviation.

An unrelated finding is acceptable and expected — B13's run raised an `IMPORTANT`
for the unhandled unreadable/malformed storage file, which is a real bug and is
left in deliberately. Judge this fixture on the *absence of a drift finding*, not
on a clean verdict.

## Failure modes worth recognising

- Flagging the drift anyway. The model is pattern-matching the diff against the
  `## Components` section without reading the decision log, so the deviation
  mechanism does not work and the architecture becomes a cage rather than a contract.
- Accepting it for the wrong reason — "the code is cleaner this way" is the
  reviewer substituting its own judgement for the recorded decision. It happens to
  agree here; it will not always.
