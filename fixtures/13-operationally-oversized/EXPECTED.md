# Expected outcome

This fixture models a milestone with only four acceptance criteria whose work
changes request cancellation, worker shutdown, background-process ownership and
live service readiness across more than three subsystems.

The orchestrator must split it before creating task packets or implementing it.
The recorded reason must include `SUBSYSTEMS_GT_3`,
`CONCURRENCY_LIFECYCLE`, and `IMPLEMENTATION_PLUS_LIVE_PROOF`.

Each child must be a useful vertical slice with its own observable outcome and
review boundary. Merely distributing criteria between component-oriented
children is not acceptable.

A nearby small coherent change that touches several files but has none of the
named complexity signals must remain one milestone.
