# V3 passing finalization

Run only after `check-review-result.py` and `transition-state.py apply-review`
have accepted a terminal same-HEAD `PASS` covering every criterion.

1. If an agreed architecture exists, invoke `harness:as-built` in RECORD mode.
   Record its returned path and one-line result in the structured state and the
   milestone `### As-Built` field without reading the artifact.
2. If no agreed architecture exists, record `NOT_REQUIRED` in both views.
3. Run:

```text
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/transition-state.py finalize \
  --state .harness/state.json --milestones .harness/milestones.md \
  --requirements .harness/requirements.md --milestone <id> --head <HEAD>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-state.py .harness/state.json \
  --milestones .harness/milestones.md --requirements .harness/requirements.md
```

4. Commit the as-built artifact and final state update together by explicit
   `.harness` paths. This is the closing commit; there must be no later
   `.harness` write hidden after it. Never use
   `git add -A`, merge, push, delete the branch, squash, reset, or stash.
5. Stop. Report milestone ID, branch, commits, validation/review/as-built paths,
   and follow-ups. Tell the human to start a fresh session for the next milestone.

No project-wide review or validation is added here.
