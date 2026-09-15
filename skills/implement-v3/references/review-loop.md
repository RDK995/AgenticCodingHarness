# V3 review loop

Use this procedure only while the current milestone is `REVIEW`.

## Dispatch

Before invoking a reviewer, check whether the exact cycle's terminal
`.result.json` already exists. Validate it with the command below. If it is valid
for the current state, criterion set, and reviewed HEAD, skip dispatch and apply
it: the previous reviewer completed its atomic write even if its prose return was
interrupted. If it is missing or invalid, continue with a fresh dispatch; never
infer a verdict from a Markdown report or `.partial.md`.

Choose the review model/effort from the current diff's recorded risk, not the
highest historical tier. Give a fresh `harness:reviewer` only requirements,
architecture when agreed, current milestone/criteria, exact diff range, affected
interfaces, validation artifact paths, and these two output paths:

```text
.harness/reviews/<milestone>-cycle<n>.md
.harness/reviews/<milestone>-cycle<n>.result.json
```

Also give it the reviewed base and HEAD, tier, model, effort, and reason code.
Never pass implementation discussion or a prior review opinion. A retry may see
the same attempt's `.partial.md` evidence pointers, which it must re-confirm.
Put `[reason: STANDARD_REVIEW] [effort: medium]` in the dispatch description, or
the named high-risk reason and high effort for an Opus review.

## Authority and interruption

The terminal `.result.json`, not prose, is authoritative. After the foreground
review call returns, run:

```text
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-review-result.py \
  .harness/reviews/<milestone>-cycle<n>.result.json \
  --state .harness/state.json --milestone <id> --head <HEAD>
```

- Missing, malformed, `complete: false`, stale-HEAD, or criterion-incomplete
  result means `INTERRUPTED`. Preserve the partial, confirm production HEAD is
  unchanged, and retry in a fresh reviewer at the same tier.
- If the terminal artifact validates but the prose response was cut off, consume
  the artifact without repeating already-complete review work.
- Allow two retries for an incomplete review. Do not increment review cycles for
  interruption.
- Never mine a partial or prose return for a verdict.

## Apply

Apply a valid result mechanically:

```text
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/transition-state.py apply-review \
  --state .harness/state.json --milestones .harness/milestones.md \
  --requirements .harness/requirements.md --milestone <id> \
  --result .harness/reviews/<milestone>-cycle<n>.result.json
```

- `PASS`: delete the partial; proceed to finalization. Do not dispatch an
  orchestrator.
- `CHANGES_REQUIRED`: delete the partial and invoke one fresh orchestrator fix
  phase with the report path, never its contents. The transition has incremented
  the completed fix-cycle count and put the milestone back `IN_PROGRESS`.
- `BLOCKED`: stop and report the result's blocked reason.

At two completed review/fix cycles with open blocking findings, stop and produce
the human escalation contract. No third cycle is automatic.
