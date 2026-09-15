# External-job handoff

Use this only for a named, approved long-running job class that cannot complete in
one bounded foreground tool call.

Record under the active milestone's `external_jobs` array:

```json
{
  "id": "stable job id",
  "class": "approved class",
  "owner": "agent role",
  "started_at": "UTC timestamp",
  "result_artifact": ".harness/evidence/<job>.json",
  "status": "RUNNING"
}
```

Never record a raw command, environment, credential, token, or secret. Launch a
job only once, persist the record, return `WAITING_EXTERNAL`, and end the
invocation. Do not sleep or poll.

On a later user-initiated invocation, inspect the named result artifact once:

- absent/incomplete: leave `RUNNING` and return `WAITING_EXTERNAL`;
- terminal success: set `COMPLETE`, record its hash/result, and resume the phase;
- terminal failure: set `FAILED`, record its safe error artifact, and route one
  bounded diagnosis task or return `BLOCKED` according to the task contract.

Unknown classes, changed result paths, or a second launch attempt are contract
failures.
