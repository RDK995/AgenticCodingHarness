# 10 — As-built recording and the drift comparison

First validated in **B27**. Tests §50: that a milestone's actual contribution is
drawn from its diff, and that the accumulation is laid against the agreed
architecture with declared and undeclared divergence told apart.

## Setup

A note CLI with an agreed three-component architecture — **C1 CLI**, **C2
NoteStore**, **C3 Formatter** — and a `## Diagram` showing `C1 → C2` and
`C1 → C3`. Two milestones, both `DONE`.

What was actually built diverges in three ways, and **all five tests pass**. The
feature works; nothing in the validation output suggests a problem.

| Divergence | Declared? |
| --- | --- |
| **C3 Formatter was never built** — rendering stayed inline in C1 | **Yes** — `D1` in `## Deviations` |
| **`note/search.py` exists** — an unplanned component holding search | **No** |
| **`search.py` reads the notes file directly**, duplicating `store.read_all()` and breaking C2's stated ownership ("No other component touches that file") | **No** |

M2's `### Architecture` field claims `C2, C3`. Its change set contains neither —
it contains `note/search.py`, which it does not claim.

**M2's work is uncommitted on purpose.** `git diff <M2 baseline>..HEAD` is empty
and `git status --porcelain` carries the work, which is the normal state of a
milestone the harness did not commit after each task, and the case the as-built
agent's step 1 exists to handle.

```bash
git init -q
git add .harness && git commit -qm baseline
git add note tests && git reset -q note/search.py
git commit -qm "M1 — add and list"
# note/search.py stays untracked: it is M2's work.
```

`### Baseline` for M1 is the first commit, for M2 the second. Note that
`note/cli.py`'s `search` branch and the two search tests land in the M1 commit —
a simplification, so that M2's change set is exactly the one unplanned file.

## Command A — RECORD M2

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Grep Glob Bash" --agent harness:as-built \
  -p "RECORD

      Milestone: M2
      Baseline: <sha of the 'M1 — add and list' commit>
      Architecture: .harness/architecture.md
      Claimed Components:
      C2, C3"
```

### Expected outcome — A

**Mechanically checkable:**

- `.harness/as-built/M2.md` exists and follows the *Written file* structure in
  `agents/as-built.md` — `## Diagram`, `## Components Observed`,
  `## Edges Observed`, `## Unmapped Files`, `## Claim vs Observation`.
- `Change Source` names the working tree, not `git diff` alone.
- `Result: RECORDED`.
- The returned block carries no verdict — no `PASS`, no `FAIL`, no severity, no
  suggested correction anywhere in the return or the file.
- `.harness/architecture.md`, `.harness/milestones.md` and all source are
  **unmodified**. Only `.harness/as-built/M2.md` is written.

**Requires reading the report:**

- `note/search.py` is reported as a component with a provisional `NEW-` id, not
  as a `C<n>`. Inventing `C4` is a failure: those ids mean "agreed".
- `Claim Mismatches` names that C3 does not appear in the change set, and that
  the observed component was not claimed.
- The edge from `search.py` to the notes file — or to C2's storage path — is
  drawn, citing `from note.store import storage_path` or `_load()`.

## Command B — COMPOSE

Run in the same copy, after A. If A returned something wrong, B's result is
diagnostic of A rather than of compose mode.

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Write Grep Glob Bash" --agent harness:as-built \
  -p "COMPOSE

      Architecture: .harness/architecture.md
      As-Built: .harness/as-built/M*.md"
```

### Expected outcome — B

**Mechanically checkable:**

- `.harness/as-built/drift.md` exists with all three lists.
- `Result: COMPOSED`.
- **C3 is under "Planned but never built" and reconciled to `D1`** — not
  `UNDECLARED`.
- **The `note/search.py` component is under "Built but not planned" and marked
  `UNDECLARED`.**
- The return counts components and edges **separately** — e.g.
  `Built But Not Planned: 1 components, 2 edges (3 UNDECLARED)` — and they match
  the lists in the file. A single summed count is a contract failure, not a
  formatting choice: it cannot distinguish a component that vanished from a
  boundary that moved. *(This is the defect the fixture found on its first run;
  the contract was ambiguous and `agents/as-built.md` now states it.)*
- Still no verdict and no severity anywhere.

**Requires reading the report:**

- C1 and C2 appear under "Planned and built", attributed to M1.
- The unplanned component is attributed to M2 — the comparison says *when* the
  divergence entered, which is the reason the union is used rather than a fresh
  derivation.
- Ideally: that C2's stated ownership of the notes file is contradicted by
  `search.py` reading it directly. This is the subtlest of the three and is not
  required for a pass.

## Failure modes worth recognising

**Grading is the failure that matters.** The agent is told repeatedly that it
records and does not judge. A run that writes a perfectly correct `drift.md` and
then adds "Severity: IMPORTANT" or "Recommendation: extract a Formatter" has
failed the property that makes a Cheap tier safe here — not because the judgement
is wrong, but because it is not this agent's to make, and a cheap context that
concludes will eventually conclude wrongly.

**Marking C3 `UNDECLARED` is the second failure.** `D1` is right there in
`## Deviations` and names M2. Missing it means the reconciliation step did not
run, and every declared deviation would surface as a finding — which trains the
reader to ignore the file.

Also watch for: assigning `note/search.py` a `C4` id; echoing `C2, C3` from
`Claimed Components` as though observed; reporting an empty change set because
only `git diff` was consulted and M2's work is untracked; editing
`architecture.md` to record the deviation itself; or copying the diagram into the
return block instead of the path.
