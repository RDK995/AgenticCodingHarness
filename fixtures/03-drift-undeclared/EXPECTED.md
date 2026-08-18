# 03 — Undeclared architectural drift

First validated in **B13** (T5). **The sharpest discriminator in the set.**

## Setup

The agreed architecture assigns persistence to **C2 — NoteStore** (`note/store.py`)
behind a C1 → C2 boundary. The implementation imports only `storage_path()` and
then does its own file I/O inline in `note/cli.py`. `store.add` and
`store.read_all` are never called: the component still exists as a file, but its
responsibility has silently moved.

`## Deviations` in `architecture.md` is empty. Nothing records that this happened.

**All four tests pass. Both acceptance criteria genuinely hold.** The feature works.
Nothing in the validation output suggests a problem, because from a behavioural
standpoint there isn't one — the defect is that the architecture no longer describes
the system and nobody decided that.

```bash
git init -q && git add -A && git commit -qm baseline
```

## Command

```bash
claude --plugin-dir /path/to/this/repo --permission-mode acceptEdits \
  --allowedTools "Read Grep Glob Bash" --agent harness:reviewer \
  -p "Review milestone M1. Inputs: .harness/requirements.md, .harness/architecture.md,
      .harness/milestones.md (M1 and its acceptance criteria), the diff since the
      baseline commit, the source under note/ and tests/, and the validation result
      'python3 -m unittest discover -s tests' => Ran 4 tests, OK. Run the validation
      yourself. Give your full report."
```

## Expected outcome

**Mechanically checkable:**

- A finding at severity `IMPORTANT` (not `OPTIONAL`, not `BLOCKER`).
- Overall verdict `CHANGES REQUIRED`.
- Both acceptance criteria still marked `PASS` in the per-criterion table.

**Requires reading the report:**

- The finding identifies that C1 bypasses C2 — that persistence is inlined in
  `cli.py` while `store.add`/`read_all` are unused — and says the deviation is
  **undeclared**.
- The reasoning is that undeclared deviation is the defect, not deviation itself.
- `BLOCKER` is *incorrect* here: the acceptance criteria genuinely pass, so this
  does not rise to the severity of failed required behaviour. `OPTIONAL` is also
  incorrect: it would not block completion, and the architecture would rot.

## Failure modes worth recognising

**Reporting `PASS` is the failure that matters, and it will look like success.**
Every test is green and every criterion is met, so a model that reviews the diff
for behavioural correctness alone finds nothing and says so confidently, with a
complete and well-formatted evidence table. There is no crash, no stack trace, and
no hedge to notice.

Also watch for: naming the drift but grading it `OPTIONAL`; flagging the dead code
as a tidiness issue without connecting it to the agreed architecture; or objecting
that filenames differ from the document, which is not drift — only a moved
responsibility is.
