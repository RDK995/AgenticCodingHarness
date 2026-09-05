# 10 — Per-milestone as-built recording

First validated in B27 and retargeted when the automatic project-level review
was removed. It tests that one milestone's actual contribution is drawn from its
committed diff and compared with what that milestone claimed, without issuing a
verdict or composing a project-wide drift report.

## Setup

A note CLI with an agreed three-component architecture and two completed
milestones. M2 claims `C2, C3`, but its committed change adds an unplanned
`note/search.py` component and does not implement C3.

```bash
git init -q
git add .harness note tests && git commit -qm baseline
BASE=$(git rev-parse HEAD)
git checkout -qb m2-search
git add note/search.py && git commit -qm "M2 T1: add search component"
```

Record `<BASE> on m2-search` as M2's baseline before running.

## Command

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Grep Glob Bash" --agent harness:as-built \
  -p "RECORD

      Milestone: M2
      Baseline: <BASE>
      Architecture: .harness/architecture.md
      Claimed Components:
      C2, C3"
```

## Expected outcome

Mechanically checkable:

- `.harness/as-built/M2.md` exists with Diagram, Components Observed, Edges
  Observed, Unmapped Files and Claim vs Observation sections.
- `Change Source` is `git diff <BASE> HEAD`; the working tree is not treated as
  the milestone's accepted change set.
- `Result: RECORDED`.
- No `.harness/as-built/drift.md` is created and `COMPOSE` is not invoked.
- The return and file contain no `PASS`, `FAIL`, severity or suggested fix.
- Architecture, milestone state and source are unchanged; only M2's as-built
  artifact is written.

Requires reading the artifact:

- `note/search.py` receives a provisional `NEW-` component ID, never an invented
  agreed `C<n>` ID.
- Claim Mismatches says C3 is absent and the observed component was not claimed.
- Any edge drawn cites code from the committed M2 range.

## Failure modes worth recognising

- Echoing claimed components as observations.
- Reading uncommitted or unrelated work as accepted milestone output.
- Editing architecture to reconcile a deviation.
- Issuing a judgement from the cheap recording role.
- Reintroducing compose mode or a project-wide drift report.
