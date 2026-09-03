# `.harness/milestones.md` template

The file opens with the ledger (below), then one block per milestone in this
exact structure:

```markdown
# Milestones

## Ledger

Current: M1
1 milestone — 1 TODO

| id | status | cycles | detail |
| --- | --- | --- | --- |
| M1 | TODO | 0 | here |

## M1 — <Outcome>

Status: TODO

### Outcome

### Architecture

### As-Built

### Acceptance Criteria
- [ ]

### Baseline

### Evidence

### Validation

### Review

### Review Cycles
0

### Follow-ups
```

Repeat the `## M<n> — <Outcome>` block for each milestone.

## The ledger

The `## Ledger` block is the file's index. Every reader's first two questions —
*which milestone is live, and where is it* — are answered by the top ten lines
instead of by reading or searching a file that reaches thousands of lines on a
real project.

```markdown
## Ledger

Current: M3
5 milestones — 2 DONE, 1 REVIEW, 2 TODO

| id | status | cycles | detail |
| --- | --- | --- | --- |
| M1 | DONE | 1 | archived |
| M2 | DONE | 0 | archived |
| M3 | REVIEW | 1 | here |
| M4 | TODO | 0 | here |
| M5 | TODO | 0 | here |
```

**Write that shape exactly**, the way the milestone headings below it are written
exactly: `Current` and the count line above the table, the header row literally
`| id | status | cycles | detail |`, four columns in that order.

- `Current` is the first milestone that is not `DONE`, or `none — all DONE`
  once the project is finished.
- `id` is the milestone id alone — `M1`, `M6a` — and **never its outcome text**.
  The outcome is one `grep` away under `## M<n> — `, it is the longest thing that
  could go in a row, and a row carrying prose is the summary-above-the-file that
  "Nothing else belongs in it" below forbids.
- `status` and `cycles` are copies of that milestone's `Status:` line and its
  `### Review Cycles` count. Nothing else goes in the row.
- `detail` is `here` or `archived`. An `archived` row's evidence is in
  `.harness/archive/M<n>.md`; its heading, `Status`, `### Outcome` and `Detail:`
  pointer are still in this file.

A ledger in a shape of its own is not a harmless variation: this block exists to
be read in one glance and checked against the body without a second lookup, and
both properties come from every reader knowing where the four cells are.

**The anchor is the heading, not a line number.** Every milestone section begins
`## M<n> — `, so `grep -n '^## M' .harness/milestones.md` returns every section
start and the ledger never has to carry one. Line numbers are the obvious thing
to put here and the wrong one: they are stale after the next edit, and a pointer
that is confidently wrong costs more than no pointer at all.

**Whoever writes a `Status:` line or a `### Review Cycles` count updates that
milestone's ledger row in the same edit**, and whoever archives a milestone flips
its `detail` to `archived`. This is the obligation writers already carry for
`### Review Cycles` — a count kept at the point of writing because no later
context can reconstruct it — applied at the top of the file as well as in the
body. Two edits, not two passes.

**A file with no ledger gets one on the next write.** Projects planned before
this block existed have milestones and no index; whoever next writes to such a
file builds the ledger from the statuses and cycle counts already in it, as part
of that edit, **in the shape above and not a reconstruction of it**. Reading the
values out is mechanical; choosing the shape is not yours to choose, and a
retrofit is exactly where an invented one gets in. Leaving it out means the next
session pays the full read this block exists to avoid.

**The body is the authority.** The ledger is an index, and an index can be stale.
Where they disagree the milestone's own section is right: correct the ledger and
carry on from the body. Never decide anything from the ledger that has a
consequence — the two-cycle cap in particular is counted from
`### Review Cycles` in the milestone itself, never from the row.

**Nothing else belongs in it.** No outcome text, no summaries, no progress notes,
no percentages. A generated summary of a file that sits above the file is a
second thing to keep true, and it is read as fact when it goes stale. Ids,
statuses, counts and `here`/`archived` are all copies of values that exist
below — they can be checked against the body in one glance, which is what makes
them safe to trust for locating.

## Valid milestone states

```
TODO
IN_PROGRESS
REVIEW
DONE
BLOCKED
```

## State transition

```
TODO → IN_PROGRESS → REVIEW → DONE
```

Use `BLOCKED` from any state whenever the milestone requires human intervention.

## Archiving settled milestones

On a long project this file accumulates the full evidence of every completed
milestone, and every session then pays to read all of it to find the one
milestone that is still open.

Once the file passes roughly **400 lines**, move the detail of **settled**
milestones into `.harness/archive/M<n>.md` — one file per milestone, content
unchanged. Leave in `milestones.md`:

```markdown
## M1 — <Outcome>

Status: DONE

### Outcome

<the outcome text, unchanged>

Detail: `.harness/archive/M1.md`
```

A milestone is **settled** when no further work will be done on it. That is
either of:

- it reached `DONE`; or
- a human explicitly closed it out short of `DONE`, and that decision is recorded
  in the milestone itself.

Both are archivable. Restricting archiving to `DONE` alone is what strands a
file: a milestone abandoned mid-flight keeps every line of its evidence forever,
and abandoned milestones are usually the largest, because they are the ones that
went wrong.

Rules for archiving:

- Never archive the active milestone, or any milestone that is `BLOCKED`.
- Never archive the **most recently settled** milestone. The milestone in
  progress most likely builds on it, so its detail is the most likely to be
  needed. This protection covers **exactly one** milestone.
- Recency is measured over **settled** milestones, not `DONE` ones. A `DONE`
  milestone that two later milestones have been settled since is no longer the
  predecessor of anything, and holding it back only makes every session read it.
  Measure by position in the run, not by whether the newer entries reached
  `DONE`.
- The protected milestone may itself be one settled short of `DONE`. Its detail
  is unlikely to be *useful*, but it is still the most recent thing the current
  work sits on top of, and protecting exactly one is simpler than reasoning about
  which kind of settlement earns it.
- Move content; never summarise or drop it. The evidence is the record of what
  was actually verified.
- Flip each archived milestone's ledger `detail` from `here` to `archived` in the
  same edit. A row still saying `here` sends the next session looking in this
  file for evidence that is no longer in it.
- Archiving moves bytes, so verify it moved them: record `wc -l` of
  `milestones.md` before and after and of the archive file written, and confirm
  they reconcile. State files have been lost to rewrites that were assumed to
  have worked.
- Below the threshold, archive nothing. A short project keeps every milestone
  here in full, matching the template above exactly.

An archived milestone is the one case where a milestone in this file does not
carry every template heading — the remaining headings are in its archive file.

## Rules

- No JSON state store, no hidden state — this file plus `requirements.md` (plus
  `.harness/archive/` once milestones have been archived, read on demand) must
  be enough for a new session to understand project status. `.harness/tasks/`
  and `.harness/reviews/` do not change that: task packets and review reports are
  scratch for a milestone in flight, written so neither is re-sent to every
  worker, verifier, retry or fix cycle that needs it. Nothing reads them to learn
  project status, and they carry no evidence — that lives here.
- `## Ledger` at the top indexes the file — id, status, cycle count and
  `here`/`archived` per milestone, plus the current pointer — and is updated by
  whoever writes a `Status:` line, a `### Review Cycles` count, or an archive
  move, in the same edit. See "The ledger" above.
- A milestone may only become `DONE` once its `Evidence` and `Validation`
  sections contain real implementation/test evidence, not a claim.
- `### Evidence` records, per task, the tier it entered at, the named reason if
  that was not Cheap, and the outcome at each rung attempted. The tier alone shows
  what was chosen; the outcome is what shows whether the choice was right, and it
  is the only record from which a human can see routing drifting upward over time.
- `### Baseline` records the commit the milestone started from, and the milestone
  branch it opened (e.g. `8b81cf1 on m0-implementation`). The orchestrator writes
  it as its first act on the implementation phase, after creating that branch and
  committing anything the tree already carried. A later phase runs in a fresh
  context and computes the milestone's diff from it, so a milestone past `TODO`
  without a baseline cannot be reviewed. Every accepted task is committed to the
  branch, so the milestone's diff is `git diff <baseline> HEAD` and nothing else;
  if `git status --porcelain` is not empty, whoever records evidence says so.
  A target that is not a git repository records that here instead, once.
- `### Review` records each cycle's verdict, the tier it ran at, and — for a
  cycle that routed corrections — a `Pre-correction: <sha>` ref taken *before*
  the cycle routed anything, and **the files those corrections changed**, calling
  out any file no finding named. `git diff <Pre-correction> HEAD` is the next
  review's scope. Filenames alone are not a diff: those files hold the milestone's
  original implementation too, which is the whole milestone under a narrower name.
  A missing ref means the next review has nothing to scope to and reads the whole
  milestone.
- `### Review Cycles` counts completed review/fix cycles for that milestone and
  is used to enforce the two-cycle cap. A cycle is a review **whose findings were
  routed and fixed**. A review that passes ends the loop and is not a cycle, so it
  does not increment this — a milestone corrected twice and then passed records
  `2`, not `3`. Counting passing reviews makes the cap unreachable. It is the only record of the count that
  survives between invocations, since each phase runs in its own context.
- `## Final Review`, at the end of the file, exists only once every milestone is
  `DONE` and the final review returned findings. It holds that loop's cycle count
  and, per cycle, the findings resolved, the pre-correction ref and the files
  changed — the same fields a milestone's `### Review` holds, for a loop that
  belongs to no milestone. Its 2-cycle cap is counted there and nowhere else.
- `### Follow-ups` records out-of-scope ideas surfaced while working the
  milestone. It is a record, not a task list — items there must not be
  implemented as part of this milestone.
- `### As-Built` holds the path to this milestone's as-built record and the
  one-line result the `as-built` agent returned (e.g.
  `.harness/as-built/M2.md — RECORDED, 3 components, 1 claim mismatch`). It is
  written once, after the milestone reaches `DONE`. **A path, never a diagram** —
  the picture lives in the file, and copying it here would make every later
  session pay to read it. Write `N/A` when the project has no `architecture.md`.
- `### Architecture` lists the component ids from `.harness/architecture.md`
  that this milestone realises (e.g. `C1, C3`). Write `N/A` when the project has
  no `architecture.md` — the field is always present so there is only ever one
  milestone template to match.
