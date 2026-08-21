# Claude Coding Harness — Implementation Plan

## 1. Objective

Build a minimal Claude Code plugin that turns rough software requirements into reviewed, tested implementation through a controlled agentic workflow:

```
Requirements
    ↓
Roast / Clarify
    ↓
Milestones
    ↓
Implement
    ↓
Test
    ↓
Fresh Review
    ↓
Acceptance Verification
    ↓
Next Milestone
    ↓
Final Fresh Review

```

The implementation should rely on native Claude Code **skills and subagents** rather than introducing a custom workflow runtime. Claude Code plugins can package skills and subagents, skills can contain reusable procedures and supporting files, and subagents operate in their own context windows.

---

# 2. Design Principles

Prioritise:

1. Simplicity
2. Clear agent responsibilities
3. Cheap-agent delegation where safe
4. Evidence over agent claims
5. Small context windows
6. Red → Green → Refactor
7. Fresh-context review
8. Explicit stop conditions
9. Protection against scope creep
10. Human escalation rather than infinite loops

Do not build infrastructure Claude Code already provides.

### V1 explicitly excludes

- Database
- Redis
- Message queues
- MCP server
- Agent SDK application
- Workflow engine
- Vector database
- Custom model router
- Parallel agent teams
- Custom persistence service
- Complex scoring system
- Hooks unless a concrete need emerges

Claude Code supports hooks and the Agent SDK, but neither is necessary for this first implementation.

---

# 3. Target Repository Structure

Create:

```
coding-harness/
├── .claude-plugin/
│   └── plugin.json
│
├── agents/
│   ├── orchestrator.md
│   ├── worker.md
│   └── reviewer.md
│
├── skills/
│   ├── roast-requirements/
│   │   └── SKILL.md
│   │
│   └── implement/
│       ├── SKILL.md
│       └── references/
│           └── engineering-practices.md
│
├── README.md
│
└── examples/
    ├── requirements.example.md
    └── milestones.example.md

```

Claude Code skills use `SKILL.md` and can contain additional supporting/reference files that load only when needed.

When used inside a target software project, create:

```
.harness/
├── requirements.md
└── milestones.md

```

These are the only persistent harness state required for V1.

---

# 4. Phase 1 — Plugin Scaffold

## Task 1.1 — Create plugin manifest

Create:

```
.claude-plugin/plugin.json

```

Give the plugin a short name such as:

```
harness

```

The plugin should expose:

- requirements skill
- implementation skill
- orchestrator agent
- worker agent
- reviewer agent

Claude Code plugins are the native packaging mechanism for reusable skills and subagents.

### Acceptance criteria

- Plugin loads successfully in Claude Code.
- Skills are discoverable.
- Agents are discoverable.
- No MCP or external runtime is required.

---

# 5. Phase 2 — Define Harness State

Implement no application code for state.

Use Markdown.

## `.harness/requirements.md`

Template:

```
# Requirements

## Goal

## Functional Requirements

## Acceptance Criteria

## Constraints

## Non-Goals

## Edge Cases

## Decisions / Clarifications

## Open Questions

```

## `.harness/milestones.md`

Template:

```
# Milestones

## M1 — <Outcome>

Status: TODO

### Outcome

### Acceptance Criteria
- [ ]

### Evidence

### Validation

### Review

### Review Cycles
0

### Follow-ups

```

## Valid milestone states

```
TODO
IN_PROGRESS
REVIEW
DONE
BLOCKED

```

### State transition

```
TODO
 ↓
IN_PROGRESS
 ↓
REVIEW
 ↓
DONE

```

Use `BLOCKED` whenever the harness requires human intervention.

### Acceptance criteria

- No JSON state store.
- No hidden state required for workflow correctness.
- A new Claude session can understand project status from the two files.
- Completed milestones contain implementation and test evidence.

---

# 6. Phase 3 — Implement `roast-requirements`

Create:

```
skills/roast-requirements/SKILL.md

```

The skill converts rough input into agreed, implementation-ready requirements.

Skills are appropriate for this because Claude Code loads their procedural instructions when the skill is invoked rather than requiring them in every session.

## Behaviour

### Step 1

Read the user's requirements.

### Step 2

Look for:

- ambiguity
- contradictions
- unstated assumptions
- unclear system boundaries
- missing failure behaviour
- missing edge cases
- unclear integrations
- missing acceptance criteria
- unnecessary complexity
- security-sensitive behaviour
- material performance constraints

### Step 3

Ask only questions whose answers could materially affect implementation.

Prefer grouped questions.

Do not ask implementation-detail questions that Claude can reasonably decide later.

### Step 4

Repeat until:

> No unresolved question is likely to materially change the implementation.

### Step 5

Present the interpreted requirements back to the human.

Require agreement before considering requirements complete.

### Step 6

Write:

```
.harness/requirements.md

```

Set:

```
## Open Questions

None

```

only when the requirements gate has passed.

---

# 7. Requirements Gate

Implementation must not start if:

```
Open Questions != None

```

or Claude believes a material ambiguity remains.

Minor technical decisions do not block implementation.

Examples that should block:

```
Should deleting an account permanently remove data?

Who is authorised to perform this action?

Does duplicate submission return the existing resource or an error?

```

Examples that normally should not block:

```
What should this internal helper function be called?

Should this private implementation use a map or array?

```

---

# 8. Phase 4 — Implement Orchestrator Agent

Create:

```
agents/orchestrator.md

```

The orchestrator controls the workflow.

Its job is **coordination**, not doing every coding task itself.

## Core responsibilities

```
Read requirements
      ↓
Inspect repository
      ↓
Create milestones if missing
      ↓
Select current milestone
      ↓
Break milestone into tasks
      ↓
Create task packets
      ↓
Route work
      ↓
Run implementation loop
      ↓
Request fresh review
      ↓
Verify acceptance criteria
      ↓
Update milestone state

```

## Orchestrator rules

The orchestrator must:

- work one milestone at a time
- minimise unrelated repository changes
- prefer existing project conventions
- delegate bounded low-risk work
- retain risky or ambiguous work
- require tests/evidence
- never mark work complete solely because another agent says it is complete
- avoid scope creep
- escalate after repeated failed review cycles

---

# 9. Phase 5 — Repository Reconnaissance

Before generating milestones, the orchestrator performs lightweight repository inspection.

Do not create another permanent agent for this.

Determine:

```
Architecture
Relevant files/modules
Existing conventions
Test framework
Build commands
Lint/type-check commands
Likely integration points
Material risks

```

Do not generate a large reconnaissance document.

The information exists to improve milestone planning.

### Acceptance criteria

Milestones must account for:

- existing architecture
- existing testing patterns
- existing public interfaces
- relevant integration boundaries

---

# 10. Phase 6 — Generate Milestones

If:

```
.harness/requirements.md exists

```

and:

```
.harness/milestones.md does not exist

```

the orchestrator generates milestones.

## Milestone rules

Milestones should represent **observable outcomes**.

Good:

```
M1 — User domain model supports account creation
M2 — User creation API is exposed
M3 — User creation is integrated with persistence

```

Bad:

```
M1 — Create files
M2 — Add classes
M3 — Write functions
M4 — Write tests

```

Tests belong inside each milestone.

## Milestone sizing

Prefer a small number of meaningful milestones.

A milestone should generally be independently:

- implementable
- testable
- reviewable

Do not generate hundreds of microtasks upfront.

---

# 11. Phase 7 — Task Packet Contract

Every delegated implementation task must use the same packet.

```
TASK

Goal:
<single bounded outcome>

Relevant Requirements:
<requirement references>

Acceptance Criteria:
- ...

Relevant Files:
- ...

Files Allowed To Change:
- ...

Constraints:
- Follow existing repository patterns.
- Do not change unrelated behaviour.
- Do not introduce dependencies unless required.
- Do not weaken tests.

Tests:
<focused validation command if known>

Return:
- Summary
- Files changed
- Tests run
- Test result
- Unresolved issues

```

The worker should receive the packet rather than the entire orchestration history.

---

# 12. Phase 8 — Implement Worker Agent

Create:

```
agents/worker.md

```

Configure it to use the cheaper Claude model intended for routine work.

Claude Code custom subagents support model configuration and are specifically suited to performing isolated work in separate contexts; Anthropic also documents cheaper-model routing such as Haiku for suitable subagent work.

## Worker responsibilities

The worker:

1. Reads its task packet.
2. Inspects only necessary context.
3. Implements the requested bounded change.
4. Runs requested focused validation.
5. Returns structured results.

## Worker must not

- redesign architecture
- broaden requirements
- implement unrelated improvements
- silently alter public interfaces
- disable failing tests
- decide unresolved product requirements
- declare the entire milestone complete

## Worker return contract

```
Summary:
...

Files Changed:
- ...

Tests Run:
- ...

Result:
PASS | FAIL | BLOCKED

Unresolved Issues:
- ...

```

---

# 13. Phase 9 — Routing Rule

Avoid numeric complexity scoring.

Use four questions:

```
Is the task clearly specified?
Is the task bounded?
Is the task low risk?
Is success easy to verify?

```

If all are effectively **yes**:

```
→ Worker

```

Otherwise:

```
→ Orchestrator

```

## Worker examples

- straightforward unit tests
- boilerplate
- simple adapters
- mechanical refactors
- renames
- documentation
- small isolated functions
- repetitive code changes

## Orchestrator examples

- architecture
- authentication
- authorisation
- security-sensitive changes
- unclear bugs
- migrations
- public API design
- cross-cutting behaviour
- tightly coupled components
- work without a clear test oracle

Risk takes priority over number of lines changed.

---

# 14. Phase 10 — Engineering Practice Reference

Create:

```
skills/implement/references/engineering-practices.md

```

Keep the file intentionally short.

## RED

```
1. Identify the behaviour being added or fixed.
2. Write or identify a test proving that behaviour.
3. Run it.
4. Confirm failure for the expected reason.

```

## GREEN

```
1. Make the smallest reasonable implementation.
2. Run the focused test.
3. Stop when required behaviour works.

```

## REFACTOR

```
1. Improve structure after tests pass.
2. Preserve behaviour.
3. Remove justified duplication.
4. Avoid speculative abstractions.
5. Re-run tests.

```

## General rules

```
Prefer small changes.

Test observable behaviour.

Preserve existing APIs unless requirements say otherwise.

Follow established project patterns.

Do not change unrelated code.

Do not weaken tests to achieve green.

Do not introduce abstractions without a current use.

Do not introduce dependencies without justification.

Run focused tests frequently.

Run broader validation before milestone completion.

```

---

# 15. Phase 11 — Implement Main Implementation Skill

Create:

```
skills/implement/SKILL.md

```

This is the primary workflow entry point.

## Algorithm

```
START

Read .harness/requirements.md

IF missing:
    tell user to run requirements workflow
    STOP

IF material open questions exist:
    STOP

Read .harness/milestones.md

IF missing:
    perform reconnaissance
    generate milestones

Find first non-DONE milestone

IF one exists:
    mark IN_PROGRESS

    inspect relevant repository context

    break milestone into bounded tasks

    FOR each task:
        create task packet

        choose worker or orchestrator

        execute Red → Green → Refactor

        run focused validation

    run milestone validation

    mark REVIEW

    invoke fresh reviewer

    process findings

    verify acceptance criteria

    record evidence

    mark DONE

    continue to next milestone

IF all milestones DONE:
    run final fresh review

IF final review passes:
    COMPLETE

```

---

# 16. Phase 12 — Test Strategy

The harness should discover existing repository commands rather than assume a particular language.

Validation hierarchy:

```
Focused test
     ↓
Module/package tests
     ↓
Type checking
     ↓
Lint
     ↓
Integration tests
     ↓
Build / broader appropriate suite

```

Only run commands the target repository actually supports.

Avoid running the full test suite after every small edit.

Before milestone completion, run the broadest **appropriate** validation available.

---

# 17. Phase 13 — Scope-Creep Guard

Add this directly to the implementation skill:

> Work not required to satisfy the current requirements or acceptance criteria must not be implemented unless necessary for correctness.

Instead add it to:

```
### Follow-ups

- Potential improvement...

```

Example:

```
### Follow-ups

- Rate limiting may be useful but is outside the current requirements.
- UserRepository could potentially be simplified separately.

```

The implementation agent must not treat follow-ups as permission to implement them.

---

# 18. Phase 14 — Implement Reviewer Agent

Create:

```
agents/reviewer.md

```

The reviewer must operate in an independent context.

Claude Code subagents have independent context windows, making a dedicated reviewer appropriate for avoiding implementation-history contamination.

## Reviewer receives only

```
Original requirements
Current milestone
Acceptance criteria
Milestone diff
Relevant surrounding code
Validation results

```

Do not pass:

- implementation discussion
- implementation rationale
- previous reviewer opinions
- worker chain-of-thought
- orchestrator justification

---

# 19. Review Boundary

Capture the git state at the beginning of the milestone.

Review the milestone change primarily from its diff.

Conceptually:

```
milestone-start
      ↓
implementation
      ↓
git diff
      ↓
reviewer

```

The reviewer may inspect surrounding code when necessary.

Do not automatically load the entire repository into the review context.

---

# 20. Reviewer Checklist

Review for:

1. Incorrect behaviour
2. Missing requirements
3. Failed acceptance criteria
4. Edge cases
5. Regressions
6. Weak/missing tests
7. Security issues
8. Unnecessary complexity
9. Violations of existing project patterns
10. Scope creep

---

# 21. Reviewer Output Contract

Use only:

```
BLOCKER
IMPORTANT
OPTIONAL

```

Every finding must include:

```
Severity:
...

Problem:
...

Evidence:
<file/location>

Why it matters:
...

Suggested correction:
...

```

Avoid vague comments.

---

# 22. Evidence-Based Acceptance Review

The reviewer must evaluate every acceptance criterion individually.

Example:

```
Acceptance Criterion:
Duplicate email returns HTTP 409.

Implementation Evidence:
src/api/users.ts maps DuplicateUserError to 409.

Test Evidence:
tests/api/users.test.ts tests duplicate submission.

Result:
PASS

```

If evidence is missing:

```
Result:
FAIL

```

Agents must not infer completion solely from another agent's summary.

---

# 23. Review/Fix Loop

```
Implementation
     ↓
Validation
     ↓
Fresh Reviewer
     ↓
 ┌──────────────┐
 │ Findings?    │
 └──────┬───────┘
        │
   YES  │  NO
    ↓   │   ↓
Fix     │ Acceptance verification
    ↓   │
Tests   │
    ↓   │
Review ─┘

```

## Maximum

Allow:

```
2 review/fix cycles per milestone

```

If BLOCKER or IMPORTANT findings remain after two cycles:

```
Status: BLOCKED

```

Return control to the human.

---

# 24. Human Escalation Contract

When blocked, provide:

```
Problem:
...

Requirement/milestone affected:
...

Attempts made:
1. ...
2. ...

Remaining issue:
...

Recommended decision:
...

```

Do not continue looping autonomously.

---

# 25. Milestone Completion Gate

A milestone may only become `DONE` when:

```
Implementation complete
        AND
Required tests pass
        AND
No BLOCKER findings
        AND
No IMPORTANT findings
        AND
Every acceptance criterion has evidence

```

OPTIONAL review findings do not block completion.

---

# 26. Record Completion Evidence

Update completed milestone:

```
## M2 — User API

Status: DONE

### Outcome

User creation API implemented.

### Acceptance Criteria

- [x] POST /users creates a user
- [x] Invalid email returns 400
- [x] Duplicate email returns 409

### Evidence

- src/api/users.ts
- src/users/service.ts
- tests/api/users.test.ts

### Validation

- npm test -- users: PASS
- npm run typecheck: PASS
- npm run lint: PASS

### Review

PASS

### Review Cycles

1

### Follow-ups

- Rate limiting is outside the current requirements.

```

This provides enough persistent context for another Claude session to resume without requiring the original conversation.

---

# 27. Phase 15 — Final Fresh Review

When every milestone is `DONE`, create another fresh reviewer context.

Provide:

```
Original requirements
All milestone outcomes
Complete implementation diff
Final validation output

```

Ask:

> Does the implementation as a whole satisfy the original requirements?

Review:

- requirement coverage
- correctness
- cross-milestone integration
- regressions
- architecture
- security
- test coverage
- unnecessary complexity
- unfinished work

Return:

```
PASS

```

or:

```
CHANGES REQUIRED

BLOCKER
...

IMPORTANT
...

```

---

# 28. Final Review Loop

If final review fails:

```
Final Reviewer
      ↓
Orchestrator
      ↓
Create bounded correction task
      ↓
Implement
      ↓
Validate
      ↓
Fresh Final Review

```

Cap the final fix/review loop at two cycles as well.

After that:

```
BLOCKED → Human

```

---

# 29. Phase 16 — README

Create a short README.

Include only:

## Install

How to load/install the plugin.

## Workflow

```
1. Run requirement roasting
2. Agree requirements
3. Run implementation
4. Harness works through milestones
5. Review final result

```

## State

Explain:

```
.harness/requirements.md
.harness/milestones.md

```

## Philosophy

```
Requirements, tests, diffs and evidence are authoritative.
Agent confidence is not.

```

Do not turn the README into a framework manual.

---

# 30. Phase 17 — Test the Harness Itself

Create a very small fixture project.

Example requirement:

```
Add a calculator function that divides two numbers.
Division by zero must return an error.

```

Use it to test the complete workflow.

## Test 1 — Requirements roasting

Confirm Claude asks what the expected error behaviour should be if it is unspecified.

## Test 2 — Milestones

Confirm Claude creates an outcome-oriented milestone rather than many unnecessary tasks.

## Test 3 — Worker delegation

Confirm a simple bounded implementation is delegated to the worker.

## Test 4 — Red/Green/Refactor

Confirm a failing test exists before the implementation passes.

## Test 5 — Reviewer

Deliberately introduce:

```
division by zero returns Infinity

```

and verify the fresh reviewer catches the requirement violation.

## Test 6 — Evidence gate

Remove the test for zero division and verify the reviewer refuses to mark that acceptance criterion as proven.

## Test 7 — Scope creep

Give the agent an opportunity to refactor an unrelated module.

Verify it records the idea under `Follow-ups` rather than changing it.

## Test 8 — Review-loop cap

Create a deliberately unresolved issue.

Verify the workflow becomes:

```
BLOCKED

```

after two unsuccessful review cycles.

---

# 31. Implementation Order

Claude should implement the plugin in this exact order:

```
1. Plugin scaffold

2. State templates

3. engineering-practices.md

4. roast-requirements skill

5. worker agent

6. reviewer agent

7. orchestrator agent

8. implement skill

9. example state files

10. README

11. fixture project / manual workflow test

12. Simplification pass

```

Do not implement all files in one uncontrolled generation step.

Validate each component before proceeding.

---

# 32. Simplification Pass

After the harness works, perform one final review specifically asking:

> What can be deleted while preserving the required behaviour?

Look for:

- duplicated instructions between agents
- unnecessary prompts
- redundant state
- unnecessary configuration
- duplicated engineering rules
- features Claude Code already provides

Prefer deletion over adding abstractions.

---

# 33. Definition of Done

The harness is complete when all of the following work:

-  Plugin loads in Claude Code.
-  Rough requirements can be roasted interactively.
-  Material ambiguity prevents implementation.
-  Agreed requirements are persisted.
-  Repository reconnaissance occurs before milestone planning.
-  Requirements become outcome-based milestones.
-  Tasks use structured packets.
-  Low-risk bounded tasks can go to the cheaper worker.
-  Risky/unbounded tasks remain with the orchestrator.
-  Implementation follows Red → Green → Refactor.
-  Scope creep goes to `Follow-ups`.
-  Tests are executed rather than merely claimed.
-  Milestone review occurs in fresh context.
-  Review uses git changes plus relevant surrounding code.
-  Acceptance criteria are mapped to implementation/test evidence.
-  BLOCKER and IMPORTANT findings prevent completion.
-  Review loops stop after two failed cycles.
-  Blocked work escalates to the human.
-  Completed milestones retain evidence.
-  Final implementation gets a fresh holistic review.
-  A new Claude session can resume using `.harness/`.
-  No additional infrastructure is required.

---

# 34. Core Invariant

The implementation should preserve one rule above all others:

> **Never trust an agent's assertion that work is complete. Verify completion from requirements, code changes, tests, and evidence.**

---

# 35. V1 Success Criterion

Do not judge V1 by how autonomous or sophisticated it appears.

Judge it by whether this sequence reliably works:

```
Human gives rough requirement
        ↓
Claude removes material ambiguity
        ↓
Claude creates sensible milestones
        ↓
Claude implements small increments
        ↓
Cheap agents handle safe bounded work
        ↓
Tests prove behaviour
        ↓
Independent reviewer finds mistakes
        ↓
Claude fixes them
        ↓
Acceptance evidence is recorded
        ↓
Final fresh review passes

```

If that works reliably, **stop adding architecture and start using the harness on real repositories.**
---

# 36. Post-V1 Addition — Architecture Design and Tracking

Sections 1–35 define V1 and are complete. This section specifies one additional
feature requested after V1 shipped. It does not modify any V1 behaviour.

## Problem

For a **new** project there is no existing architecture to inspect, so Phase 5
reconnaissance has nothing to find and Phase 6 milestones — which are deliberately
outcome-shaped, not implementation-shaped — carry no architectural content.

Because `skills/implement/SKILL.md` invokes a **fresh** orchestrator per milestone,
each one independently invents whatever architecture its milestone needs. Nothing
holds those choices consistent across milestones, and no record exists that a
decision was ever made or why.

## Solution

A third harness state file, `.harness/architecture.md`, agreed with the human
before milestones are generated, and enforced during review.

```
requirements.md  →  architecture.md  →  milestones.md  →  implementation
   (what/why)         (how)              (in what order)
```

## `.harness/architecture.md`

Produced by a new `architect` skill. Human-confirmed, not auto-generated: an
architecture Claude alone chose and then measures itself against is self-marking
homework, and the same material-ambiguity principle that governs requirements
applies to datastore, boundary, and sync/async decisions.

Components carry `C<n>` identifiers so milestones can reference them.

## Optional, not mandatory

If `.harness/architecture.md` is absent, the harness behaves exactly as in V1.
This keeps existing-repository work unaffected — architecture is *decided* for new
projects, whereas for an existing codebase it is *discovered* by Phase 5
reconnaissance, which already exists and must not be duplicated.

## Two coverage gates

When the file exists:

- every functional requirement maps to at least one component
- every component is realised by at least one milestone

## Tracking

Each milestone declares which components it realises. Progress against the
architecture is **derived** from milestone status. Do not add a second
per-component status field — that is redundant state.

## Reviewer input

This amends the closed list in Phase 14 ("Reviewer receives only") by one item:
`.harness/architecture.md`, when it exists. It is an agreed artifact like
`requirements.md`, not implementation rationale, so it does not weaken the
fresh-context boundary.

## Drift

Deviation from the declared architecture is not inherently wrong; **undeclared**
deviation is. A justified change is recorded in the `## Deviations` log with its
reason. A silent one is an `IMPORTANT` review finding, which blocks milestone
completion under the existing Phase 25 gate and is resolved either by correcting
the code or by recording the deviation.

## Acceptance criteria

- Architecture is proposed from agreed requirements and requires explicit human
  agreement before it is written as `AGREED`.
- Milestones generated against an architecture reference the components they realise.
- Both coverage gates are checked.
- The reviewer detects undeclared drift and reports it as `IMPORTANT`.
- A recorded deviation does not produce a finding.
- With no `architecture.md` present, V1 behaviour is unchanged.

---

# 37. Post-V1 Addition — Runtime Contract

Sections 1–35 define V1. This section, like §36, specifies a post-V1 addition. It
changes no behaviour.

## Problem

The harness is a Claude Code plugin, but almost none of it is Claude-specific:
the task packet contract, routing rule, engineering practices, evidence tables,
finding contract, completion gate, escalation contract and all four templates are
runtime-neutral text.

That portability is accidental rather than stated. Nothing records what the
harness actually requires from the runtime hosting it, so anyone evaluating a
different runtime — or a different model behind the same runtime — has to
reverse-engineer the assumptions from the agent definitions.

## Solution

Document the coupling; do not remove it.

- `docs/runtime-contract.md` states the primitives the harness requires, the
  capability each role demands of its model, the substitution points, and the
  ways a substitution fails silently.
- Residual prose using "Claude" as a synonym for "the agent" becomes
  runtime-neutral wording.

## What must not change

`agents/worker.md` keeps `model: haiku`. Phase 8 requires the worker to run on
the cheaper model, and B5 records that frontmatter line as the evidence for that
acceptance criterion. Removing the pin would silently promote every delegated
task to the session model — a cost regression and a spec violation. The line is a
documented substitution point, not a default to delete.

## Acceptance criteria

- No plugin file uses "Claude" as a synonym for the agent.
- `agents/worker.md` frontmatter is byte-for-byte unchanged.
- The runtime contract names the required primitives, the per-role capability
  tiers, and the silent-failure modes.
- Claude Code behaviour is unchanged, proven by re-running validation rather than
  asserted.

---

# 38. Post-V1 Addition — Retained Fixtures

## Problem

B11 and B13 validated sixteen behaviours against fixtures built in scratch
directories. The fixtures were not retained, so their evidence is a written
description rather than something re-runnable.

That is tolerable for a one-off build and unworkable for comparing models: every
run would re-derive the starting state by hand, and two runs would not be
comparing the same thing.

## Solution

Retain the discriminating scenarios under `fixtures/` as **templates**.

A fixture is a starting repository state plus a verified-correct expected
outcome. Running one mutates the directory, so a fixture is copied out to a
scratch location and run there; the retained copy is never the thing that runs.
This needs no reset script and no runner.

## Scope

Retain the scenarios that discriminate between a capable agent and a plausible
one, not every check ever run. A fixture whose failure mode is obvious from the
output teaches nothing that a golden path does not.

## Acceptance criteria

- Each fixture states the command to run and the verified-correct outcome.
- Each fixture records which milestone originally validated it.
- Expected outcomes distinguish mechanically checkable facts from judgements that
  require reading the agent's report.
- At least one fixture is executed from its retained state, proving the retained
  copy is sufficient to reproduce the scenario.

---

# 39. Post-V1 Addition — Bounded Token Cost

## Problem

Measured across this repository's own build sessions (693 assistant turns,
`~/.claude/projects/-Users-ryankenny-Projects-codingHarnessV2/*.jsonl`):

| Measure | Value |
| --- | --- |
| Total context consumed | 97.7M tokens (95.0M cache-read, 2.6M cache-write) |
| Output tokens | 0.64M |
| Median context per turn, long sessions | 140k–160k |
| Turns above 200k context | 162 |
| Share of spend from turns already above 100k | **84%** |
| Compactions | 0 |
| Subagent turns | **0** |

Three causes, in order of size.

**Marathon sessions.** Two sessions ran 333 and 297 turns without a reset. Once
a session is at 150k, every subsequent turn re-pays for that window, so cost
grows with the square of session length rather than with work done.

**No delegation.** Zero subagent turns means every bounded task ran inline in the
main context at the session tier, rather than in a fresh worker context on the
cheap tier. The routing rule existed and was never exercised.

**Monotonic state files.** `.harness-dev/progress.md` reached 952 lines (~11k
tokens) holding the full detail of fifteen completed milestones, and the operating
protocol reads it first, every session. `.harness/milestones.md` grows the same
way in a real project, so the cost ships to users.

None of this is caused by the size of the harness's own instructions: the entire
repository is ~36k tokens.

## Solution

Bound the context each role holds, rather than shortening what any role reads.

1. **Milestone boundaries are context boundaries.** A completed milestone ends the
   session. `progress.md` already exists so a fresh session can resume without the
   conversation; the protocol must say so.
2. **Delegate by default.** The routing rule decides *who* does the work, and the
   default for bounded low-risk work is a fresh subagent, not the current context.
3. **State files carry the current milestone, not the archive.** Completed
   milestone detail moves to one file per milestone, referenced by an index and
   read only on demand. This applies to both `.harness-dev/progress.md` and, for
   users, `.harness/milestones.md`.
4. **Reads are section-scoped.** Locate the section, then read that range — do not
   read a 1600-line specification to answer a question about one milestone.
5. **Roles name their model tier.** `runtime-contract.md` §Capability tiers already
   assigns each role a tier; only the worker's was pinned in a file. The rest
   inherited the session model, which both overpays for the orchestrator and leaves
   the reviewer — the tier explicitly identified as the one to protect — silently
   downgraded whenever the session model is cheap.

## Scope

No new infrastructure: no token accounting, no budget enforcement, no
configuration system, no runner. The changes are to instructions, state layout,
and three frontmatter lines.

Splitting state files must be lossless. Completed milestone evidence is the
repository's record of what was actually verified; it is relocated, never
summarised or dropped.

## Acceptance criteria

- The session-start read is bounded and does not grow with the number of
  completed milestones.
- Completed milestone detail is retained in full and reachable, proven by
  reconstruction rather than assertion.
- The operating protocol states when to end a session and when to delegate.
- Specification reads are section-scoped, with the mechanism stated.
- Every role's model tier is named in a file rather than inherited, and matches
  the tier `docs/runtime-contract.md` assigns it.
- The reviewer is not downgraded.

## Amendment — tier assignment inverted by decision (2026-08-20)

The final criterion above no longer holds, by explicit human instruction after
B16's implementation was complete: `orchestrator` is pinned to `opus` and
`reviewer` to `sonnet`, inverting the assignment this section argued for.

What survives unchanged is the criterion that matters structurally — each role's
tier is *named in a file* rather than inherited from the session. That was the
actual defect §39 identified: a role's tier being a side effect of how the
session started. Which tier each role gets is a decision; that it is recorded at
all is the requirement.

The risk the original argument described is not resolved, only relocated. A weak
reviewer still fails silently rather than loudly, so the orchestrator's
independent re-verification — now the higher-tier pass, and the one that runs
first — carries proportionally more of the guarantee. `docs/runtime-contract.md`
§Capability tiers records this, and names `fixtures/01-requirement-violation` and
`fixtures/03-drift-undeclared` as the empirical check on whether the reviewer
role still holds at the lower tier.

# 40. Post-V1 Addition — Tier Assignment and Escalation

## Problem

B16 pinned every role's model tier in a file rather than letting it be inherited
from the session. That fixed the mechanism — a role's tier became a recorded
decision — but left two questions open that are not about context cost and do not
belong to §39.

**Which tier each role gets.** §39 argued the reviewer belonged at the top tier
because nothing verifies the verifier. That was a reasoned position, not a
measured one, and it was never tested against the fixtures that exist to test it.

**What happens when the cheap tier cannot do the work.** The worker retry ladder
ran three fresh-context attempts at one tier and then handed the task to the
orchestrator. There was no intermediate rung: a task slightly beyond the cheap
tier fell all the way to the most expensive agent in the system, which is both
the slowest path and the one that puts work back into the context §39 exists to
keep small.

## Solution

1. **Assign tiers by decision and verify the assignment.** `orchestrator` runs at
   the highest tier because it holds routing, independent re-verification, and
   escalation judgement, and it re-verifies every worker claim before evidence is
   recorded. `reviewer` runs below it. The reviewer's capability to hold its role
   is an empirical question, so it is settled by running
   `fixtures/01-requirement-violation` and `fixtures/03-drift-undeclared` rather
   than by argument.

2. **The retry ladder climbs tiers rather than repeating one.** Three attempts at
   the Cheap tier, then two at the High tier, then the orchestrator. Repeating a
   failed tier a third time tests patience, not capability.

3. **Escalation is a per-invocation model override, not a second agent.** Same
   instructions, same tool restrictions, same task-packet contract, more
   capability. Editing `model:` in `agents/worker.md` to achieve the same effect
   would promote every delegated task permanently and invert the economics the
   routing rule protects.

4. **Climbing stops when capability is not the problem.** Repeated failures caused
   by an unclear or contradictory requirement do not become resolvable at a higher
   tier; they escalate to the orchestrator or the human instead.

## Scope

No new infrastructure. The changes are the two frontmatter pins, the retry ladder
in `agents/orchestrator.md`, one packet field in `agents/worker.md`, and the
corresponding entries in `docs/runtime-contract.md`.

This adds required primitive **5** — per-invocation model override — to
`docs/runtime-contract.md`. It is the only primitive with a clean degradation: a
runtime lacking it skips the escalated rungs and goes Cheap → orchestrator.

Verification is by existing fixtures. No fixture is added.

## Acceptance criteria

- Every role's pinned tier matches the tier `docs/runtime-contract.md` assigns it,
  and the document records the assignment as a decision rather than a derivation.
- The reviewer's tier is verified against fixtures 01 and 03, not asserted.
- The retry ladder is tier-climbing, with the attempt counts per tier stated.
- Escalation is documented as a model override, with the "do not edit the
  worker's `model:` line" rule stated and its consequence explained.
- The runtime contract names the override primitive and its degradation path.
- The ladder has a documented early exit for failures that more capability cannot
  fix.
- ~~The tier-climbing ladder is exercised end to end by an orchestrator run.~~
  **Waived — see below.**

## Amendment — the ladder-exercising criterion is waived (2026-08-20)

`fixtures/06-impossible-criterion` was built to satisfy that criterion and does
not. Its task is impossible by construction, so that it would fail deterministically
rather than depending on a capability gradient — but the orchestrator declined to
delegate it at all, recording that a task with no honest implementation mainly
gives a worker the opportunity to special-case the pinned test. It implemented the
task itself, proved the impossibility, and escalated. That is the correct
engineering outcome; it simply is not the one the criterion asked for.

The two requirements pull against each other. To climb the ladder a task must be
**delegable and still fail** — which means genuine coding difficulty, which is
exactly the model-dependent gradient §40 set out to avoid. A fixture that pinned
"the Cheap tier fails here and the High tier succeeds" would drift with every model
release and could never distinguish a working ladder from a lucky sample.

The criterion is therefore waived rather than met, on this reasoning:

- **The failure mode is mild.** If the ladder instruction is misread, behaviour
  degrades to what it was before §40 — the orchestrator takes the task itself.
  Slower and more expensive, not unsound. Contrast the reviewer tier, where the
  failure mode is a silent false `PASS` and the gate opening on nothing; that one
  justified two fixture runs and got them.
- **The mechanism is instruction, not code.** There is no branch that can be wrong
  in a way review cannot see.
- **The gap is recorded, not implicit.** `fixtures/README.md` states that the
  ladder is unexercised and why, so nobody later closes it with the gradient
  fixture this section argues against.

What `06` does verify — impossibility proved rather than asserted, the ladder
deliberately not spent, the pinned test intact, and an escalation a human can act
on — is retained as its purpose.

# 41. Post-V1 Addition — Read Discipline at Runtime

## Problem

Observed on a real project immediately after adopting B16/B17: the orchestrator's
first turns consumed ~93k tokens before any implementation work began. The project's
harness state was `architecture.md` 500 lines, `milestones.md` 639, `requirements.md`
297 — roughly 1,400 lines read in full before planning started.

B16 measured that 84% of spend came from turns already above 100k. A session that
*starts* at 93k has spent its entire margin on reconnaissance.

Three specific causes, all of them gaps in how B16 was applied rather than new
defects.

**The archive threshold is checked at the wrong end of the milestone.**
`agents/orchestrator.md` applies the ~400-line archiving rule "before you finish",
when recording completion evidence. So an oversized `milestones.md` is read in full
at the *start* of every milestone and only trimmed at the *end*. The read that costs
the most is the one that happens before the rule fires.

**Agents re-read their own definitions.** An agent's instructions are already in its
system prompt. Reading `agents/<self>.md` from disk duplicates 100-330 lines that
were never absent.

**Ranged reads never reached the runtime roles.** §39 item 4 required
section-scoped reads and was applied to `CLAUDE.md` — this repository's own build
protocol — and to nothing the agents read. `grep -rln "sed -n" agents skills docs`
returned no matches. The roles that read a user's 500-line `architecture.md` had no
instruction to read part of it.

## Solution

1. **Check the archive threshold on open, not only before finishing.** The
   orchestrator archives an oversized `milestones.md` when it first reads it, so the
   saving applies to the session that pays for it. The end-of-milestone check stays.

2. **Never re-read your own definition.** Stated in each agent file. Reading
   *another* role's file for a contract it must produce remains correct.

3. **Ranged reads for reference documents, with the review material exempt.**
   Locate the section, read that range. This applies to large state and reference
   documents. It explicitly does **not** apply to the diff, code, or tests under
   review: a reviewer that samples the material it is judging produces exactly the
   confident, evidence-shaped `PASS` that `docs/runtime-contract.md` identifies as
   the harness's worst failure. Cheapening reconnaissance is safe; cheapening
   verification is not.

## Scope

Instructions only. No new infrastructure, no configuration, no change to any state
file format. The archiving mechanism itself is unchanged — only when it is checked.

## Acceptance criteria

- The archive threshold is checked when `milestones.md` is first read, and still
  before the milestone completes.
- Every agent file states that an agent must not re-read its own definition.
- Ranged-read guidance is present in the agent files, not only in `CLAUDE.md`.
- The guidance explicitly exempts material under review from ranged reading.
- No fixture regresses; `05` and `06` still behave as their `EXPECTED.md` files say.

# 42. Post-V1 Addition — Reduce the Per-Turn Constant

## Problem

Measured over one full milestone of `fixtures/05-golden-path` (142 assistant
turns, 2,882,600 tokens of context):

| Role | Model | Turns | Base | Peak | Total | Fixed |
| --- | --- | --- | --- | --- | --- | --- |
| orchestrator | opus | 41 | 17,944 | 41,085 | 1,151,579 | 63.9% |
| main driver | opus | 22 | 18,518 | 39,343 | 560,978 | 72.6% |
| worker | haiku | 35 | 8,809 | 14,811 | 417,525 | 73.8% |
| reviewer | sonnet | 20 | 11,003 | 20,963 | 327,256 | 67.2% |
| **all** | | **142** | | | **2,882,600** | **70.4%** |

**70.4% of all spend is the fixed baseline re-paid on every turn** — system
prompt, tool definitions, agent definition — not accumulated conversation and not
file reads. Growth is the minority of the bill.

Two consequences follow, and neither is addressed by any earlier milestone.

**The agent definition is a per-turn constant.** Baseline tracks definition size:
`orchestrator.md` 422 lines → 17.9k base, `reviewer.md` 188 → 11.0k, `worker.md`
125 → 8.8k. The orchestrator's definition costs roughly 3.4k tokens on each of its
54 turns in that run — about 184k tokens for one small milestone. Every line in
that file is billed once per turn, forever.

**Turn count multiplies everything resident.** 54 orchestrator turns to deliver a
four-line function. Halving turns halves spend regardless of what is in context.

This also settles a question raised while measuring: resetting context between
*tasks* rather than milestones would attack only the 29.6% growth while re-paying
an ~18k baseline per reset, and there is no per-task durable record to resume
from. It is rejected on the measurement, not on preference.

## Solution

1. **Delete duplication from `agents/orchestrator.md`.** B12's question, applied
   to the file with the highest per-turn cost: what can be removed while
   preserving required behaviour? Bullets that restate a section appearing later
   in the same file are the clearest case — several say "see X below" beside the
   thing they summarise.

2. ~~**Prefer batched tool calls.**~~ **Tried and removed — see the amendment
   below.** Turn count is the largest lever in the table above, but an instruction
   is not a mechanism for pulling it, and this one measurably did not.

## Scope

Deletion and compression of instructions. No behaviour is removed: every rule the
fixtures verify must survive, and the fixtures are the check.

Guard against the obvious failure — trimming a definition until the behaviour it
encodes stops happening. Anything deleted must either be stated elsewhere in a
file the role already reads, or be genuinely redundant.

## Acceptance criteria

- `agents/orchestrator.md` is materially smaller, with the before/after recorded.
- No rule verified by a fixture is lost; each deletion is redundant or relocated.
- ~~Brief batching guidance is present.~~ **Withdrawn** — added, measured, found
  to have no effect, and removed rather than kept on the strength of its rationale.
- `fixtures/05` and `06` still meet their `EXPECTED.md` outcomes.
- The measured orchestrator baseline is recorded after the change, from a real
  run rather than estimated.

## Amendment — measured result, and the batching instruction withdrawn (2026-08-20)

B19 was proposed on the reasoning that turn count is the dominant lever: at 70.4%
fixed cost, cutting turns 30% would save ~21% of spend. Measured against both
fixtures, that is not what happened.

| Fixture | Context before | after | Turns |
| --- | --- | --- | --- |
| `06` (single thread, clean signal) | 501,870 | 480,309 | **−4.3%**, 22 → 22 |
| `05` (full workflow) | 2,882,600 | 2,864,174 | **−0.6%**, 142 → 135 |

Neither increased, so the milestone stands. But the split matters:

**The deletion pass works and is small.** `orchestrator.md` 422 → 353 lines; the
measured baseline fell 703/turn on `06` and 918/turn on `05`. On `06` — identical
turn counts, no subagent variance — that accounts for essentially the whole
−4.3%.

**The batching instruction did nothing and has been removed.** Turn count was
unchanged on `06` (22 → 22). On `05` the orchestrator dropped 54 → 49 turns, but
the driving session rose 22 → 27 and +136k tokens, and `SKILL.md` was untouched by
B19 — so that movement is run-to-run variance, and the −5 cannot be credited to
the instruction either. Meanwhile the paragraph cost ~50 tokens on every turn,
about 2.4k per milestone, indefinitely.

Keeping it would have meant paying a certain cost for an unmeasurable benefit,
which is the exact failure mode §42 was written to attack. It was removed on its
own evidence.

**Total context could not be measured this way.** Four samples of `06` — two of
them the same commit on the same fixture — put turn count at 22/22/28/24 and total
context across a 33% band. The per-fixture percentages quoted above are each one
paired sample inside that band, and do not support a total-spend claim. What is
stable is the baseline (5.0% spread, mean −799 tokens/turn after the trim) and
context per turn (sd 386 on ~22.5k). B19 claims the baseline reduction only.

A consequence for anyone pursuing the turn lever: at 27% run-to-run variance on an
identical task, a mechanism aimed at turn count cannot be validated by paired
fixture runs. It needs repeated sampling with a stated sample size.

**What the measurement was actually worth was the diagnosis, not the fix.** Agent
prose explains only 27% of the orchestrator's baseline gap over the worker
(2,508 tokens of 9,135); the remainder is system prompt and tool definitions — the
worker declares 6 tools, the orchestrator is unrestricted by design. The largest
per-turn constant in the system is therefore not reachable by editing
instructions, and no further deletion pass should be expected to pay much.
# 43. Post-V1 Addition — Enforced Delegation and a Milestone Budget

## Problem

Measured on a real project (`OpenWeightHarness`, 7 orchestrator runs, 1,542
orchestrator turns, 262,532,486 tokens):

| Turns | Total | Fixed | Growth | Growth % |
| --- | --- | --- | --- | --- |
| 15 | 528,375 | 323,775 | 204,600 | 39% |
| 191 | 31,208,829 | 4,234,852 | 26,973,977 | 86% |
| 251 | 41,373,941 | 5,588,515 | 35,785,426 | 86% |
| 264 | 58,941,246 | 5,960,328 | 52,980,918 | 90% |
| 331 | 62,230,743 | 7,796,374 | 54,434,369 | 87% |
| **all** | **262,532,486** | **34,891,072** | **227,641,414** | **87%** |

One milestone took 1h09m and 41.4M tokens. §42 found growth to be 36% of a
41-turn orchestrator run and concluded the per-turn constant was the target;
**at 191-331 turns growth is 82-95%**, and the constant is the rounding error.
The conclusion of §42 does not generalise past short milestones, and this section
supersedes it as the account of where the money goes.

The cause is not milestone scope. Across those same runs:

- **21 delegations against 218 `Edit`/`Write` calls the orchestrator made itself** —
  a 1:10 ratio. Implementation output therefore lands in the orchestrator's own
  context, which is the context that compounds.
- **~45% of turns issue no tool at all.**
- **0 of 832 tool-issuing turns issued more than one tool.**

Splitting a milestone that still runs inline yields two smaller milestones with
the same defect. Retained work is the cause; milestone size is the symptom.

B16 already required delegation by default, and B16 was measured on this
repository finding zero subagent turns. The instruction has now failed twice.
`docs/runtime-contract.md` states the reason plainly: a per-role restriction is
"a property of the runtime, not a promise in the prompt. A runtime that cannot
enforce it downgrades a guarantee to a request." Delegation has been a promise in
the prompt, and it was declined nine times in ten.

## Solution

**1. Make delegation structural, not advisory.** The orchestrator declares no
`tools:` line and is unrestricted. Give it a restricted set without `Write` and
`Edit`, so implementation cannot happen in its context.

This requires somewhere for escalated work to go, because today the ladder ends
with "do the task yourself". Replace that final rung with a **worker invoked at
the top tier**: the orchestrator's own model, a fresh context, the same task
packet contract. Work then always runs in a subagent, at a tier matching its
difficulty, and never in the coordinating context.

The trade is real and must be stated: an escalated worker does not carry the
orchestrator's accumulated understanding of the milestone, only its packet. That
is already true of every other delegation, and the packet contract exists to carry
what is needed — but the orchestrator currently escalates to itself *because* it
holds that context, and this gives that up deliberately in exchange for the 87%.

**2. Give a milestone a stated budget, counted in acceptance criteria.**
`CLAUDE.md` has required 3-7 bounded tasks per milestone since B16; no agent file
says it, so no runtime milestone has ever been planned against it — the same
dev-side-only gap B18 closed for ranged reads.

Measured on the same project, milestones carry **7 to 13 acceptance criteria**
(M6: 13, M7: 12, M4: 9); the retained fixtures carry 2-4. A 13-criterion milestone
is not 3-7 tasks — each criterion needs an implementation, a test and recorded
evidence — so it is 20-40, and a 250-turn context is its arithmetic consequence.

Express the budget in **acceptance criteria**, not tasks. Criteria are fixed at
generation time, are visible in `milestones.md` afterwards, and can be checked by
a human or the reviewer without observing the run. A task budget is a promise; a
criteria count is an artifact. Target 3-5 criteria; past 7, it is two milestones —
decided during generation rather than discovered at turn 250.

Size and retention multiply rather than compete. A 13-criterion milestone run
inline *is* a 250-turn context. Fixing delegation alone leaves the orchestrator
accumulating 13 criteria worth of packets, results and verification; fixing size
alone leaves smaller milestones still running inline. §43 requires both, and
neither is sufficient on its own.

**3. Record what actually happened.** Each completed milestone records its task
count and how many tasks were delegated. Without it there is no way to tell
whether any of this changed behaviour, and §42 showed that reasoning about
expected effect is not a substitute.

## Scope

Frontmatter, instructions, and one line per milestone in the template. No token
accounting, no budget enforcement machinery, no runner.

The escalation change removes the orchestrator's ability to implement. That is
the point, and it is the only part of this section that is a mechanism rather
than a request.

## Acceptance criteria

- `agents/orchestrator.md` declares a `tools:` set without `Write` or `Edit`.
- The retry ladder's final rung is a top-tier worker invocation, not the
  orchestrator implementing inline; `docs/runtime-contract.md` records the change
  and its trade.
- A stated budget of acceptance criteria per milestone, with a split rule, in a
  file the orchestrator reads; and the existing "prefer a small number of
  meaningful milestones" wording reconciled with it, since it currently biases
  the opposite way.
- `milestones.md` records tasks planned and tasks delegated.
- Fixtures 01-06 still meet their `EXPECTED.md` outcomes — in particular `06`,
  whose current expectation is that the orchestrator implements the task itself,
  and which must be re-examined rather than assumed to still hold.
- Re-measured on a real milestone, with the delegation ratio and growth share
  reported before and after.

# 44. Post-V1 Addition — Milestones Are Thin End-to-End Slices

## Problem

Milestones generated by the harness come out shaped like components, not like
behaviour. On a real project (`OpenWeightHarness`), the milestone list runs:
worktree isolation, then repository interrogation, then a tool registry, then a
sandbox, then a mutation vocabulary, then a rollback pipeline — and only then
"a single coding agent completes `/code` end to end", carrying 12 acceptance
criteria. Every integration risk in the project is deferred into that one
milestone.

Nothing about that is an accident. `agents/orchestrator.md` teaches it directly.

**The worked example is horizontal.** The section labelled `Good:` reads:

```
M1 — User domain model supports account creation
M2 — User creation API is exposed
M3 — User creation is integrated with persistence
```

Domain, then interface, then storage. Nothing is demonstrable end to end until
M3, and M1 cannot be exercised through any entry point a user of the system has.
It is presented as the pattern to imitate.

**The architecture coverage gate enforces the same shape.** Milestones are
"sequenced to realise its components", `### Architecture` lists "the component ids
it realises", and "every component must be realised by at least one milestone".
Read together, those map milestones onto components roughly one-to-one, which
produces horizontal slices by construction regardless of what the examples say.

A horizontal plan defers all integration evidence to the end, which is where it is
most expensive to act on. It also produces exactly the milestone shape §43 was
trying to shrink: a component takes as many criteria as the component has
surface, rather than as few as a behaviour needs.

Note that §43's criteria budget does not fix this and can worsen it: splitting one
oversized component milestone yields several smaller *component* milestones, which
is thinner but no more demonstrable.

## Solution

1. **Replace the worked example with a walking skeleton.** The first slice is the
   thinnest path that runs end to end; later slices deepen it. Every example in
   the file should be demonstrable through a real entry point.

2. **Require demonstrability.** Every milestone carries at least one acceptance
   criterion exercised through the system's real entry point — a CLI invocation,
   an HTTP request, a public API call — not solely a unit test of internals. If
   the only way to demonstrate a milestone is a unit test of a component, it is a
   component milestone and must be re-cut. This is checkable in `milestones.md`
   after the fact, like the criteria budget.

3. **Reconcile the coverage gate with slicing.** A slice *advances* components
   rather than *realising* them; a component is legitimately built across several
   slices, deliberately partial or stubbed early. The gate becomes: every
   component is exercised by at least one milestone. A component nothing exercises
   is still a planning gap.

4. **Order by risk.** The first slice proves the riskiest integration, not the
   easiest layer.

## Scope

Instructions in `agents/orchestrator.md`, and the coverage-gate wording. No change
to the template, the state files, or any fixture's expectations.

## The safeguard this must not break

Slicing creates pressure to cut *through* component boundaries rather than across
them — inlining persistence in the CLI because it is the shortest path to a
working slice. That is exactly `fixtures/03-drift-undeclared`, the sharpest
discriminator in the set: all tests pass, every acceptance criterion holds, and
the architecture silently stops describing the system.

Thin does not mean shortcut. A slice crosses every boundary the architecture
defines; it just crosses each one shallowly. Under slicing the drift check matters
more, not less, and `03` must still fail anything that dissolves a boundary.

## Acceptance criteria

- The worked example demonstrates a walking skeleton, not a layer sequence.
- A demonstrability rule is stated, naming the real entry point.
- The coverage gate permits a component to be advanced across several milestones
  and no longer implies one milestone realises one component.
- Slice ordering by integration risk is stated.
- The boundary safeguard is stated where slicing is taught, not only in the
  architecture section.
- Re-planned on real component-shaped milestones, and the result is slices — each
  with an entry-point criterion — with scope conserved.
- `fixtures/03` and `04` still behave as their `EXPECTED.md` files say; `05` and
  `06` unaffected.

# 45. Post-V1 Addition — A Planning Fixture, and Generation Gates

## Problem

Fixtures 01-06 test review and execution. **Nothing tests planning.**

Every change to milestone generation in §43 and §44 was validated by re-cutting one
real project's board by hand. That does not generalise to another project, does not
survive a model change, and will not catch a drift back to layered milestones.
Milestone quality — the input to everything else the harness does — is the one
behaviour with no fixture.

The absence shows in what §44 produced. Re-cut against real requirements, 13 of 16
milestones were genuine end-to-end slices, and three were not:

- **Driving through an entry point is not the same as asserting observable
  behaviour.** One milestone drives `/think` — a real entry point — and asserts
  that context assembly follows the order exact search → filename match → LSP →
  Tree-sitter → imports → lexical ranking. A user cannot tell if that order
  changed. It satisfies the letter of the demonstrability rule and misses its
  point. Two others do the same with internal loop structure and DAG persistence.

- **Thinness is nominal while a single criterion can carry a subsystem.** One
  entry-point criterion requires creating an isolated worktree, reading the
  repository, editing files, running tests, and returning a diff. Three-to-five
  criteria per milestone looks thin until one of them is an entire coding agent.

- **Ordering by integration risk is stated and not applied.** The resulting board
  is ordered by dependency and feature area; the riskiest integration sits ninth
  of sixteen.

The pattern across §43, §44 and B16 is consistent: **prose advises, gates decide.**
§44 worked only because it changed the coverage gate; its examples alone would have
been overridden at the point of enforcement. B16's delegation instruction was pure
advice and has failed twice, measured at 1:10 on a real project.

## Solution

Build the fixture first, then the gates, so the gates have something to be measured
against rather than being hand-checked on one board.

**1. `fixtures/07-layered-temptation`.** Requirements plus an agreed
`architecture.md` whose components map cleanly onto tiers — the shape that invites
one milestone per component. No `milestones.md`: generation is the thing under test.

The discriminator is mechanical and does not depend on the domain. In a layered
plan each milestone names about one component and components do not recur. In a
sliced plan each milestone names several components and the same component is
advanced by several milestones. That distinction is countable from the
`### Architecture` fields.

~~**2. Demonstrability becomes a gate, and tests the assertion rather than the
driver.**~~ ~~**3. One assertion per criterion.**~~ **Both withdrawn — see the
amendment below.** The fixture was built first precisely so the gates would have
something to be measured against, and it showed the failure they targeted does not
occur in fresh generation.

## Scope

One fixture, and gate wording in `agents/orchestrator.md`. No new infrastructure.

Adding examples is explicitly rejected: §44 already demotes the layered example to
`Bad` and still produced three weak slices.

## Acceptance criteria

- `fixtures/07-layered-temptation` exists: requirements, an agreed architecture
  with tier-shaped components, no `milestones.md`, and an `EXPECTED.md` separating
  mechanical checks from those needing the report read.
- Its mechanical checks include component recurrence across milestones and a
  criteria cap, and do not depend on the fixture's domain.
- Baseline recorded: what the harness generates for it **before** the gates.
- ~~The demonstrability gate tests the assertion, not the driver.~~ **Withdrawn.**
- ~~The one-assertion rule is stated.~~ **Withdrawn.**
- Fixture 07 meets its `EXPECTED.md` on the agents as they stand, and 03, 04, 05,
  06 are unaffected.

## Amendment — baseline passed, gates withdrawn (2026-08-21)

`fixtures/07-layered-temptation` was run against the agents **before** any gate
change. It passed 5 / 5 mechanical checks and every report-level expectation.

```
M1 — A posted URL can be followed through the API and survives restart   5   C1,C2,C3,C4,C5
M2 — A custom alias can be claimed, and only once                        4   C1,C2,C3
M3 — A link stops redirecting once it expires                            4   C1,C2,C3,C4
M4 — Followed links are counted and reported by the stats endpoint       5   C1,C2,C3
```

M1 is a walking skeleton. Every milestone crosses at least two components, C1 and
C2 recur in all four, all five components are covered, and every milestone carries
an HTTP entry-point criterion. Criteria are single assertions about observable
behaviour — `302` with a `Location` header, `400` and creates no link, `410` with
no `Location`. None carries a subsystem. It also declined the fixture's central
trap, folding restart-survival into the skeleton rather than turning five
acceptance criteria into five milestones.

The gates were proposed from three weak slices observed on a real project. Those
came from **re-cutting existing component milestones**, which is a different and
harder task than planning from scratch, and the weakness does not reproduce in
generation. Adding a gate would mean paying a permanent per-turn cost — in the file
§42 measured — for a failure with no reproduction. Both were withdrawn on that
evidence, as §42's batching instruction was.

What survives is the fixture, which is the part that generalises: it locks in
current planning behaviour, its discriminators are domain-independent, and it will
catch a regression under a future model or prompt change.

The weak-slice observation is retained as an under-specified follow-up rather than
a fix: it is reproducible only on re-cuts. If it recurs, a re-cut-specific fixture
is the right response, not a gate on generation.