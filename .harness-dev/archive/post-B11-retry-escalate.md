## Post-B11 enhancement: task-level retry-then-escalate

Status: DONE (supplementary to the 12 tracked build milestones — user-requested
after B11, applied to already-`DONE` B5/B7 as a scoped runtime behavior change,
not a re-opening of those milestones)

### Change

Per user request: each task delegated to the `worker` gets up to 3 fresh-context
attempts (each a brand-new subagent invocation, not a continuation, with a
"Previous Attempt(s)" block appended to the task packet on retries so the
attempt is informed rather than blind) before escalating. Escalation target is
the **orchestrator itself** (not a separate stronger-model tier), since it's
already the higher-authority, unrestricted-tool agent in this system, and 3
failed attempts is itself a signal the task was misrouted as bounded/low-risk.

### Files changed

- `agents/orchestrator.md` — new "Task-level retry and escalation" subsection
  under "Implementation loop".
- `agents/worker.md` — task packet contract extended with an optional
  "Previous Attempt(s)" field; instruction to read it on retries and not
  assume prior partial work is still on disk.

### Validation

Fixture (`fixture-escalate/`, outside `~/.claude/`): a task packet with an
internally-contradictory constraint (Goal requires creating `text_utils.py`;
`Files Allowed To Change` lists only a nonexistent `other_file.py`), routed to
the worker per the normal routing rule.

Result: PASS — the full policy executed correctly:
1. **Attempt 1**: worker implemented the goal correctly (9/9 tests passing)
   but silently violated the file-scope constraint and self-reported PASS.
   Orchestrator's independent validation caught the violation and rejected it
   — did not trust the worker's claim.
2. **Attempt 2**: a genuinely fresh worker, given the "Previous Attempt" note,
   correctly identified the same contradiction and returned `BLOCKED` with no
   changes — proof the retry context propagated and was used, not ignored.
3. **Attempt 3**: a third fresh worker reconfirmed the same finding.
4. **Escalation**: orchestrator took the task over itself, independently
   re-confirmed via `git log`/`ls` that the constraint was truly unsatisfiable
   (not just hard), correctly declined to unilaterally rewrite the packet's
   own fields (that would be deciding an unresolved product/spec question
   rather than a capability problem), cleaned up the rejected Attempt-1
   artifacts, and produced a complete Human Escalation Contract — including
   noting a working implementation already existed and just needs the
   constraint clarified.

Independently verified outside the session: `find . -not -path './.git*' -type
f` → only `README.md`; `git status --short` → clean. The repo was left exactly
as claimed, not just described as clean.

### Decisions

- Confirmed the escalation target should stop and escalate to the *human*
  rather than silently resolve an ambiguity itself, even with full authority
  — this wasn't explicitly spelled out in the new retry-and-escalation text,
  but the orchestrator correctly derived it from the existing "never trust...
  decide unresolved product requirements" rules already in the agent files.
  No further doc change needed; the existing rules already covered this case
  correctly under real pressure.
- Did not add an explicit stronger-model tier (e.g. pinning `opus` for one
  extra worker attempt before falling to the orchestrator) per the earlier
  discussion — kept to the simpler orchestrator-as-escalation-target design to
  avoid adding a new model-selection concept the plan doesn't otherwise have.

### Follow-ups

None.
