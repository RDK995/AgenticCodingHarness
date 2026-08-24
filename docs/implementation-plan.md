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

> **Superseded by §49.** The four questions below survive; the burden of proof
> inverts. Requiring all four to be "yes" before using the Cheap tier was measured
> routing 0 of 12 real tasks there.

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

~~**1. Make delegation structural, not advisory** by removing `Write` and `Edit`
from the orchestrator.~~ **Withdrawn — re-specified as §46.** The orchestrator must
write `.harness/milestones.md`, which is the evidence the completion gate reads;
and it must keep `Bash` to re-run validation independently, which means it can
write any file regardless. A tool restriction here is a nudge, not a mechanism.
See §46 for the replacement.

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

- ~~`agents/orchestrator.md` declares a `tools:` set without `Write` or `Edit`.~~
  **Withdrawn — see §46.**
- ~~The retry ladder's final rung is a top-tier worker invocation.~~ **Subsumed
  by §46**, which routes every task rather than only the escalated one.
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

# 46. Post-V1 Addition — Route Everything, Choose the Tier by Risk

## Problem

§43 measured, on a real project, that 87% of orchestrator spend is accumulated
growth rather than the per-turn constant, and that the orchestrator made 218
`Edit`/`Write` calls itself against 21 delegations. It concluded that delegation
had to be made structural by removing the orchestrator's edit tools.

That conclusion was wrong on three counts, and the third matters most.

**The orchestrator has to write.** Recording status, criteria, evidence,
validation and review outcome into `.harness/milestones.md` is its job, and that
record is what the completion gate reads. An orchestrator that cannot write cannot
close a milestone.

**A tool restriction is not enforcement while `Bash` is present.** The orchestrator
needs `Bash` to re-run validation independently — the core invariant is that no
claim is trusted without verification it performs itself. With `Bash` it can write
any file. Removing `Write` and `Edit` is a speed bump.

This also corrects `docs/runtime-contract.md`, which claims the reviewer "has no
`Write` or `Edit`, so it can only ever report findings and never quietly fix what
it is judging. That is a property of the runtime, not a promise in the prompt."
The reviewer declares `tools: Read, Grep, Glob, Bash`. A reviewer with `Bash` can
edit. The guarantee is weaker than stated, and §43 leaned on that overstatement.

**The 1:10 ratio may be the routing rule being obeyed, not ignored.** The rule
tells the orchestrator to keep "architecture, authentication, authorisation,
security-sensitive changes, unclear bugs, migrations, public API design,
cross-cutting behaviour, tightly coupled components". The measured project is a
coding harness containing a policy engine, a sandbox seam and worktree isolation —
a large share of its work lands squarely in those categories. Reading 1:10 as
non-compliance was an assumption, not a finding.

## Solution

The defect is not that the orchestrator **retains** work. It is that retained work
runs **in the coordinating context**, which is the context that compounds.

So stop deciding *who* does the work, and decide *at what tier it runs*:

1. **Every task is delegated.** The orchestrator plans, routes, verifies and
   records. It does not implement.

2. **Risk chooses the tier, not the venue.** Bounded, clearly-specified, low-risk
   work goes to the Cheap tier. Architecture, security-sensitive changes,
   cross-cutting behaviour, ambiguous bugs and public interfaces go to a worker at
   the **top tier** — the orchestrator's own model, a fresh context, the same task
   packet contract. The guarantee the routing rule protects is preserved: risky
   work still gets maximum capability. Only the venue changes.

3. **The retry ladder collapses into the same rule.** Cheap-tier failures escalate
   by tier as today; the final rung becomes a top-tier worker rather than the
   orchestrator implementing inline. When that also fails, the task is blocked and
   goes to a human — the orchestrator has no implementation of its own to fall
   back on.

4. **No tool restriction.** It would not enforce anything, and it would break
   evidence recording. Delegation is a rule about how the orchestrator works, and
   the honest description of it is a rule, not a guarantee.

## The trade, stated plainly

A top-tier worker receives a task packet, not the orchestrator's accumulated
understanding of the milestone. The orchestrator currently retains cross-cutting
work *because* it holds that context, and this gives that up.

That is the whole bet: that a packet plus a fresh read of the repository is enough
for work the routing rule calls risky, and that the 87% is worth it. It is a bet,
not a derivation, and if it is wrong the symptom will be more review cycles on
retained-class work rather than a visible failure.

## Scope

Instructions in `agents/orchestrator.md`, the retry ladder, and a correction to
`docs/runtime-contract.md`'s overstated tool-restriction claim. No frontmatter
change, no new agent file, no infrastructure.

## Acceptance criteria

- The routing rule chooses a tier for every task; no task is retained for the
  orchestrator to implement.
- The top tier is reachable for the categories the rule previously told the
  orchestrator to keep.
- The retry ladder's final rung is a top-tier worker, and exhaustion escalates to
  a human rather than to the orchestrator implementing.
- `docs/runtime-contract.md` no longer claims tool restriction prevents a
  `Bash`-capable role from writing, and says what it actually provides.
- Fixtures 05, 06 and 07 still meet their `EXPECTED.md` outcomes. `06` is the one
  at risk: its expectation is that the orchestrator implements the task itself and
  explains why it did not delegate.
- The delegation ratio and orchestrator growth share are re-measured on a real
  milestone, before and after.
# 47. Post-V1 Addition — Three Worker Tiers, and a Reviewer That Matches the Work

## Problem

Two defects in the tier scheme, both introduced by earlier sections of this plan.

**There is no middle tier for work.** §46 routes every task, but only to Cheap or
Top: `haiku` or `opus`. The reviewer runs at `sonnet` and no worker ever does. A
task too risky for `haiku` and not architectural jumps straight to the most
expensive model in the system, which is the majority of ordinary implementation
work.

**The reviewer can be weaker than the work it reviews.** B16 pinned the reviewer
at one fixed tier; B17 set that tier to `sonnet`. §46 then routed risky work to a
worker at `opus`. The result is a `sonnet` reviewer passing judgement on `opus`
work — exactly the failure `docs/runtime-contract.md` names as the worst available
to this system: a weak reviewer does not fail loudly, it emits a confident
per-criterion `PASS` and the completion gate opens on nothing.

A fixed reviewer tier cannot be correct, because the tier of the work is decided
per task at routing time and is not known when the reviewer's frontmatter is
written.

## Solution

**1. Three worker tiers.**

| Tier | Model | For |
| --- | --- | --- |
| Cheap | `haiku` | Bounded, clearly-specified, low-risk, easily verified |
| Mid | `sonnet` | Ordinary implementation that is none of those, but not architectural |
| Top | `opus` | Architecture, security, cross-cutting behaviour, public interfaces, ambiguous bugs, no clear test oracle |

**2. The ladder is `Cheap ×2 → Mid ×1 → Top ×1`, then blocked.** Four attempts
rather than five, and each rung is a genuine capability increase instead of a
repeat. A task routed to Mid starts at that rung; a task routed to Top gets its
one attempt there. Exhaustion escalates to a human.

**3. The reviewer runs at no less than the highest tier that produced the work.**
`sonnet` reviews `sonnet` and `haiku`; `opus` work is reviewed by `opus`. The
orchestrator records the highest tier used in the milestone and invokes the
reviewer at that tier, using the per-invocation override that
`docs/runtime-contract.md` already requires as primitive 5. The final holistic
review runs at the top tier, because it covers work from every tier.

`agents/reviewer.md` keeps `model: sonnet` as the floor — the tier used when a
milestone is entirely Cheap or Mid work.

## Scope

The routing rule, the ladder, and the review invocation in
`agents/orchestrator.md`; the final review in `skills/implement/SKILL.md`; the
tier table in `docs/runtime-contract.md`. No frontmatter change, no new agent
file.

## Acceptance criteria

- Routing selects one of three tiers, with the criteria for each stated.
- The ladder is Cheap ×2 → Mid ×1 → Top ×1 → blocked, and a task routed above
  Cheap enters at its own rung.
- The reviewer is invoked at no less than the highest tier used in the milestone,
  and the final review at the top tier.
- The milestone records the tier each task ran at, so the review tier is
  auditable after the fact rather than asserted.
- `docs/runtime-contract.md` describes the reviewer tier as derived from the work
  rather than fixed.
- Fixtures 05, 06 and 07 still meet their `EXPECTED.md` outcomes, and 06's ladder
  wording is updated to the new counts.

## Amendment — the degradation analysis was wrong (2026-08-21)

§47 and `docs/runtime-contract.md` both claimed that a runtime lacking the
per-invocation override "would review top-tier work at the reviewer's pinned
tier". That is self-contradictory: routing to the top tier uses the same
primitive, so a runtime without it has no top-tier work to mis-review. Total
absence degrades safely — everything runs at `haiku`, `sonnet` reviews it, and the
reviewer remains stronger than the work.

The real risk is narrower and worse. **Partial support** — the override honoured
for workers but not the reviewer, or `worker.md` pinned upward while the reviewer
stays fixed — violates the pairing with nothing reporting it. **Silent support** —
a runtime that accepts the model parameter and ignores it — is worse still: the
orchestrator records `Review tier: opus` while `sonnet` ran, so the evidence
asserts a pairing that never happened.

The asymmetry is the point. A silently ignored override in the ladder fails
loudly: the attempt runs weaker, fails, the task blocks, nothing false is
recorded. The same failure at the reviewer is silent — a confident `PASS`, an
opened gate, and a milestone recording a review that did not occur.

`runtime-contract.md` now states this, and requires confirming from the transcript
that an override actually changed the model before trusting the pairing on a new
runtime. Where it cannot be confirmed, pin the reviewer to the top tier: a known
cost beats an unverifiable guarantee.
# 48. Post-V1 Addition — The Coordinating Context Is the Cost

## Problem

§43 measured 87% context growth and blamed retained implementation. §46 removed
retained implementation. **The growth is still 87%.**

Measured on `openCodeOpenWeightHarness` M1 — the first milestone planned under the
§44 slice rule and the §43 criteria budget, and the first run under §46/§47
routing. Method: every `assistant` message in the session transcript and its
`subagents/*.jsonl`, counting `input + cache_creation + cache_read + output`
tokens per turn; `fixed` is the smallest context observed multiplied by the turn
count, and `growth` is the remainder.

**One milestone. Four acceptance criteria. 18 contexts, 2,039 turns,
221,806,363 tokens.**

| Context | n | Turns | Tokens | Share |
| --- | --- | --- | --- | --- |
| **orchestrator** | 2 | 548 | **107,246,808** | **48.4%** |
| worker | 12 | 1,097 | 77,885,133 | 35.1% |
| reviewer | 3 | 262 | 21,588,436 | 9.7% |
| skill session | 1 | 132 | 15,085,986 | 6.8% |

The M1 orchestrator alone: **527 turns, 106,281,674 tokens, 87% growth, peak
context 370,706, median 199,638.** Half its turns ran above 200k; 18% ran above
300k. For comparison, §43's seven orchestrator runs averaged 37.5M and peaked at
62.2M each — and those milestones carried 7 to 13 criteria. This one carried four.

**The three fixes already applied all worked, and none of them moved the number.**

- *Retained implementation is gone.* The orchestrator made 17 `Edit` calls and
  **all 17 were to `.harness/milestones.md`.** Zero source edits. §43's 1:10
  delegation ratio is now 15 delegations against 0 retained implementations.
- *The milestone was thin.* Four criteria, inside the §43 budget, demonstrated
  end to end through the adapter — a §44 slice, not a component build-out.
- *Routing worked.* 12 workers and 3 reviewers, tiers recorded per task.

So the cause is not what the work is, nor who does it. It is that **one context
holds the whole milestone from planning to completion**, and every later turn
re-pays for all of it.

Four things fill that context, in order of size.

**1. The review/fix phase runs at peak context and costs more than everything
before it.** Splitting the orchestrator run at its first reviewer invocation:

| Phase | Turns | Tokens | Share |
| --- | --- | --- | --- |
| Planning through implementation | 306 | 40,771,418 | 38% |
| Review/fix cycles | 221 | **65,510,256** | **62%** |

The cheapest turns run first and the most expensive run last, because the review
phase pays for the implementation phase on every single turn. B20 recorded this as
an open question — "4x the milestones means 4x the review cycles… unverified either
way." It is now verified, and it is unfavourable.

**2. Verification is paid twice.** The orchestrator spent 72 tool calls verifying
work itself (29 git inspections, 18 file reads, 14 greps, 11 test/type-check runs).
The three reviewers then spent 117 `Bash` calls doing it again — independently, in
fresh contexts, which is exactly what they are for. Both are correct under the
current instructions; together they are redundant, and only one of them happens in
a context that compounds.

**3. Delegated work returns through the front door.** Of the orchestrator's 58
`Read` calls, **52 were on subagent `.output` files and 6 were on repository
files** — several output files read three to six times each. Delegation is supposed
to keep a worker's reading out of the coordinating context; re-reading its full
output transcript puts the expensive half back. It also means the orchestrator's
"independent verification" leans on the agent's own report, which the core
invariant forbids.

**4. Turns that do nothing are not free.** **62% of the orchestrator's 527 turns
issued no tool at all** — §43 measured ~45%, so this is worse, not better. At a
median 199,638-token context, 326 tool-free turns are roughly 65M tokens of pure
re-payment. 23 further `Bash` calls were sleeps and polling loops waiting on
backgrounded subagents; each poll re-pays the full context to learn nothing.

**The design already anticipated the fix and never used it.**
`agents/orchestrator.md` describes itself as coordinating "one milestone at a time
(**or one review/fix correction cycle**)" — a correction cycle as a *separate
invocation*. `skills/implement/SKILL.md` instead says "invoke harness:orchestrator
to run that milestone to completion", one invocation from reconnaissance to `DONE`.
The 62% is the cost of that gap.

## Solution

**1. A milestone is more than one orchestrator invocation.** `SKILL.md` drives
phases, not milestones: plan → implement → review/fix (per cycle) → complete. Each
is a fresh orchestrator context that reads `.harness/milestones.md` and writes back
to it. This is not new infrastructure — it is the handoff the file already provides
for a fresh human session, and the invocation shape `orchestrator.md` already
describes. The review/fix cycle is the one that must be separate; the others are
worth it if the same measurement says so.

**2. The orchestrator retains verdicts, not evidence.** Per-task verification moves
to a fresh context that receives the task packet, the claimed result and the diff,
re-runs validation, and returns a verdict with its evidence for the record. The
orchestrator writes the evidence to `milestones.md` without the diff and test
output ever entering its context. The core invariant is unchanged — an independent
context still checks every claim, which is precisely what the reviewer already does
and what the orchestrator currently duplicates. What changes is that the checking
does not happen in the context that compounds.

This needs its own agent rather than reusing the reviewer, on three grounds.
`reviewer.md` is written end to end around a *milestone* — the diff since milestone
start, the acceptance criteria, architecture drift, a per-criterion evidence table,
graded findings — so aiming it at one task means overriding most of its
instructions in the invocation, which is the failure `runtime-contract.md` already
names: an instruction in a prompt is a request, not a property. Its tier is derived
and floors at `sonnet`, so reusing it would put fifteen `sonnet`-or-higher contexts
into a milestone to re-run fifteen commands. And keeping the roles distinct is what
stops a task-level check being mistaken for the milestone review that opens the
gate.

The new role is Cheap on purpose, **and that is the one part of this section that
is not obviously safe.** §47 answered fabricated evidence by having the
orchestrator re-run validation at the top tier; moving the re-run to `haiku`
changes what that answer promises. The mitigation is structural rather than
capability-based — the verifier did not write the code, cannot edit it, returns a
command and an exit status rather than a judgement, and a tier-matched reviewer
re-runs everything before the gate — but the mitigation is an argument, and this
plan has been wrong about arguments three times. It needs a fixture that plants a
false `PASS` and checks the verifier contradicts it; `01` and `03` discriminate the
reviewer role and do not cover this one.

**Do not delete per-task verification instead of moving it.** It looks like the
cheaper simplification — the milestone reviewer would eventually catch the same
defects — but the retry ladder depends on knowing that an *attempt* failed in
order to escalate a tier. Without a per-task verdict a lying `PASS` advances the
milestone, and the failure surfaces at review as a correction task rather than as
a tier escalation, which is the mechanism §47 built.

**3. Never read a subagent's `.output` file.** The invocation returns the result;
the file is the full transcript. Read the repository to verify a claim, not the
claimant's account of it.

**4. Do not background a worker and poll for it.** A blocking invocation costs one
turn; polling costs a turn per check at full context.

**5. Correct `agents/orchestrator.md`'s description**, which still says the
orchestrator "routes tasks to the worker or handles risky work itself" — withdrawn
by §46 and contradicted by the routing rule twenty lines below it. §47 recorded
"no 'do it yourself' instruction survives anywhere"; the orchestrator's own
frontmatter is a counterexample.

**6. Check the milestone's size and shape when it is picked up, not only when it
is planned.** §43's criteria budget and §44's slice rule are both subsections of
"Generating milestones", which fires only when `.harness/milestones.md` does not
exist. `SKILL.md` then picks the first milestone that is not `DONE` and runs it,
whatever shape it is in. A plan written before those rules — or by a generation
run that got them wrong — is never re-examined, and the same defect runs on every
project that has one. `OpenWeightHarness` M5 is the worked example: 7 criteria,
one component (C9), no criterion exercised through an entry point, run exactly as
planned long after both rules existed.

The gate belongs where the milestone is picked up, and reuses the thresholds
already stated rather than restating them: 1-5 run it, 6-7 run it and note the
size, 8 or more split it before running anything. A milestone with no criterion
demonstrable through a real entry point fails on shape.

Two different failures, needing two different responses. **Oversize is a
mechanical split** the orchestrator performs itself — suffix rather than
renumber (`M6` → `M6a`, `M6b`), conserve every criterion exactly, split on the
outcome, and then *return without implementing*, so the parts are run by fresh
contexts rather than by the one that just did the planning. B20 validated exactly
this operation on a real 13-criterion milestone: 13 criteria in, 13 out, none
lost, none added, cut along real boundaries. **Wrong shape is a re-cut**, which
reorganises criteria into slices and may reword them — a planning decision with no
obviously correct answer, so it escalates to a human rather than happening
silently.

## Scope

`skills/implement/SKILL.md`, `agents/orchestrator.md`, and one measurement script
under `.harness-dev/`. No runner, no token accounting at runtime, no new agent file
unless per-task verification proves to need one rather than reusing the reviewer.

This is the fourth section to target this number. §42 targeted the per-turn
constant, §43 retained implementation and milestone size, §46 who does the work.
Each fixed something real and left the number where it was. **Reasoning about
expected effect has now failed three times and is not acceptable as evidence here.**

## Acceptance criteria

- A milestone's review/fix cycles run in orchestrator contexts separate from the
  one that planned and implemented it, and `milestones.md` carries enough state for
  the fresh context to resume without the original conversation.
- Per-task verification happens in a context other than the orchestrator's, and the
  orchestrator's recorded evidence is unchanged in substance by the move.
- A fixture plants a worker return claiming a `PASS` that is false, and the
  verifier contradicts it. Without this the Cheap pin is an untested assumption
  and `runtime-contract.md` must say so. Two shapes, both of which a passing test
  command hides: a criterion the command does not exercise, and a claimed change
  that never landed.
- The orchestrator may stop before routing anything only when it demonstrates the
  blocker rather than asserting it. Concluding a milestone impossible is the one
  move that routes around "every task is delegated" by never creating a task, and
  the demonstration is what separates judgement from avoidance.
- No instruction anywhere directs the orchestrator to read a subagent's `.output`
  file; the polling pattern is named and forbidden.
- `agents/orchestrator.md`'s description matches its routing rule.
- A milestone is checked for size and shape when it is picked up, not only when
  it is generated; an oversized one is split before any task runs, with criteria
  conserved exactly and later milestone numbers left valid; a wrong-shaped one
  escalates rather than being silently re-cut.
- Fixtures still meet their `EXPECTED.md` outcomes — in particular `02` and
  `06`, which drive the orchestrator directly and whose single-shot invocation
  cannot reach a review cycle once phases are separate.
- The two-cycle review/fix cap has a fixture that tests it directly. `02` reached
  the cap by way of contradictory criteria and no longer does — the harness now
  escalates before routing anything — so the cap has been uncovered since §46
  without that being visible. A fixture that starts at `Review Cycles: 2` with an
  open finding tests the cap itself, and with it the B25-specific risk that the
  count only survives between phases through `milestones.md`.
- **Re-measured on a real milestone by the same method**, reporting orchestrator
  share, peak and median context, growth share, tool-free turn share, and
  `.output` reads, against the M1 baseline above. Targets: orchestrator share
  below 25% (from 48.4%), peak context below 200,000 (from 370,706), tool-free
  turns below 45% (from 62%). A run that does not move these has not satisfied
  this section, whatever else it improves.

## Caveats on the baseline

M1 ran **three** review cycles, not the two the cap allows, and ended `BLOCKED`; a
milestone that passes at cycle 1 or 2 is cheaper than this. The 62% review-phase
share is therefore an upper bound on that particular figure. The orchestrator's
87% growth, its 48.4% share, the 52-of-58 `.output` reads and the 62% tool-free
turns are not sensitive to the third cycle. Comparisons with §43 are across
different projects and tasks; the method is identical, the conclusion does not rest
on a small difference, and no §43 run approached this one's cost.


# 49. Post-V1 Addition — Cheap by Default

## Problem

**The Cheap tier has never run a task on a real milestone.** M1 of
`openCodeOpenWeightHarness` routed 12 workers: 4 to `opus`, 8 to `sonnet`, **0 to
`haiku`**. §47 built three tiers and the cheapest one is unused, so the ladder's
first two rungs are decoration and every real task starts at `sonnet` or above.

Three causes, all visible in `agents/orchestrator.md` §Routing rule as it stood.

**It was an AND of four judgements.** Cheap required *all four* of clearly
specified, bounded, low risk and easily verified to be "effectively yes". Any one
falling short dropped the task to Mid. On real work something is nearly always
slightly unclear, so the compound probability of clearing four gates is low by
construction — the rule did not have to be disobeyed to produce this result.

**The text said to default upward.** The description of Mid ended: "This is where
most implementation belongs." That sentence is an instruction, and it was obeyed.

**Nothing pushed back.** Routing up is never penalised. The orchestrator runs at
the top tier, decides on behalf of a worker it never observes, has no record of
the Cheap tier's success rate, and sees no cost signal. A failed cheap attempt
looks like a mistake it caused; routing up looks like prudence. There is no
counter-pressure anywhere in the file, and an upward drift is invisible.

## Solution

**1. Invert the burden of proof.** Cheap is the default. The four questions
remain, asked the other way round: name which one fails and why, or route Cheap.
"It seemed safer" is not a reason. The named reason goes in the packet, so the
judgement is auditable rather than felt.

**2. Name the work that is Cheap regardless of the milestone.** A risky milestone
does not make its mechanical tasks risky. Tests written from an assertion the
packet already states, decision records, renames, exports, fixtures, stubs behind
a settled interface, repetitive changes, small isolated functions with a stated
input and output — Cheap unless there is a reason *this instance* is not. The
§47 examples already gestured at this and read as illustration; they become a
rule. Top stays Top, unchanged.

**3. Price a failed Cheap attempt.** The ladder already budgets two of them; the
orchestrator does not behave as though spending one is acceptable. Put the
measured numbers in the file — Cheap ~285k tokens against Mid's 1.0-11.4M and
Top's 6.9-10.8M, from this project's own runs — and state the asymmetry plainly:
a wrong guess downward costs one cheap attempt, a wrong guess upward costs the
whole difference on every task routed that way, and fails silently. Routing up is
the expensive choice, not the cautious one.

**4. Record the outcome, not just the tier.** §47 records which tier ran each
task. It does not record whether that rung *succeeded*. The tier shows what was
chosen; the outcome shows whether the choice was right, and it is the only record
from which upward drift is visible. Without it there is nothing to tune on and the
default reverts to whatever feels safe.

## Scope

`agents/orchestrator.md` §Routing rule and its evidence-recording instruction; one
rule in `milestones-template.md`; the `worker` row in `docs/runtime-contract.md`.
No new agent, no frontmatter change, no mechanism — the pins and the ladder are
exactly as §47 left them.

## Acceptance criteria

- Cheap is stated as the default, and going above it requires a named reason
  recorded in the packet.
- A category list makes mechanical work Cheap independent of the surrounding
  milestone's risk.
- The relative cost of the tiers, and the asymmetry between guessing down and
  guessing up, are stated where the routing decision is made.
- Each task's record carries the rung it entered at, the reason if not Cheap, and
  the outcome at each rung attempted.
- Fixtures 01-09 still meet their `EXPECTED.md` outcomes.
- **Re-measured on a real milestone: the Cheap tier runs a non-zero share of
  tasks, reported as a count against the total.** §48's lesson applies here
  exactly — three sections in a row have argued a cost improvement into existence
  and left the measured number unmoved. A run that routes 0 of N to Cheap again
  has not satisfied this section, whatever else it improves.

# 50. Post-V1 Addition — The Architecture Is Drawn, and What Was Built Is Drawn Back

## Problem

§36 gave the harness an agreed architecture and a drift check, and both work:
`architecture.md` names components `C1…Cn`, milestones reference the components
they realise, and the reviewer raises `IMPORTANT` when a milestone's diff departs
from the agreed design without a recorded deviation.

Three things are still missing, and they are the same thing seen from three
angles.

**The agreed architecture is prose, so nobody can see its shape.** Components,
boundaries and dependencies are stated in sentences spread over four sections. A
reader has to reconstruct the graph in their head to answer "what talks to what",
which is the question the document exists to answer.

**Nothing records what a milestone actually built.** The reviewer judges drift
and then discards its working — the finding survives, the picture does not. By
the fifth milestone there is no accumulated account of the system as constructed,
only a document describing the system as intended plus a list of deviations that
were noticed at the time.

**Drift is only ever checked one milestone at a time.** Each milestone's diff is
compared to the agreed architecture in isolation. A responsibility that migrates
one small step per milestone never trips a per-milestone check, and there is no
point at which the whole built system is laid against the whole agreed one.

## Change

Draw the agreed architecture. Draw what each milestone actually built. Compare
the accumulation to the original at the end.

### The planned diagram

`architecture.md` gains a `## Diagram` section: a Mermaid `flowchart` with one
node per component and one edge per dependency, edge-labelled with what crosses
that boundary.

It is a **rendering of sections that already exist**, not a new decision — nodes
come from `## Components`, edges from their `Depends on` lines, labels from
`## Interfaces`. It therefore cannot disagree with the text; if it does, the
document is internally inconsistent and that is itself the finding. The architect
writes it in Step 5 and the human agrees it with the rest.

### The as-built record

A new agent, `harness:as-built`, runs **once per milestone, after it reaches
`DONE`**, in its own context pinned to the Cheap tier. It reads the milestone's
diff from its `### Baseline`, derives which components the changed files actually
constitute, and writes `.harness/as-built/M<n>.md` — a Mermaid diagram of that
milestone's contribution plus the observations behind it.

Two properties are load-bearing.

**It records; it does not judge.** It reports what the diff shows and where that
contradicts what the milestone claimed, and stops there. No verdict, no severity,
no correction. Judging stays with the reviewer, which is what makes a Cheap pin
safe here for the same reason §48 argued it safe for the verifier: an agent that
cannot conclude anything cannot conclude anything wrong.

**Its output never enters the orchestrator's context.** The agent writes the file
itself; the orchestrator records the path and a one-line result. §48 measured 52
of 58 orchestrator `Read`s going to subagent output files, and a diagram is a
large artifact to re-pay for on every subsequent turn. The milestone record
carries a pointer, not a picture.

### The comparison

Before the final review, `harness:as-built` runs once more in **compose mode**:
it unions every `.harness/as-built/M<n>.md` into the system as actually built and
lays it against `## Diagram` and `## Components`, writing
`.harness/as-built/drift.md` with three lists — *planned and built*, *built but
not planned*, *planned but never built* — each entry reconciled against the
`D<n>` entries in `## Deviations`.

The union is used rather than a fresh derivation from the finished tree because
it is free (the artifacts already exist) and because it carries attribution: it
says not only that a boundary moved but which milestone moved it. The cost is
that it inherits any error a milestone made — which is why the compose step
reports disagreements between milestones rather than silently merging them.

`drift.md` becomes an input to the final review. Undeclared divergence is an
`IMPORTANT` finding, exactly as §36 already grades it; a divergence reconciled to
a recorded deviation is not a finding at all. **The comparison is a report, not a
new gate** — it gives the reviewer evidence it previously had to reconstruct, and
changes no completion criterion.

## What this costs

One Cheap context per milestone, plus one at the end. Measured Cheap-tier cost is
~285k tokens, so a ten-milestone project adds roughly 3M — about 1.3% of the
221.8M §48 measured for a single milestone of `openCodeOpenWeightHarness`, and
under 1% of a whole build. The constraint that keeps it there is the context
boundary above: the moment a diagram is read into the orchestrator or the
reviewer's planning context, it stops costing 285k once and starts costing its
own size on every following turn.

## Acceptance criteria

- An agreed architecture carries a `## Diagram` whose nodes and edges match its
  `## Components` and `## Interfaces` exactly.
- Each `DONE` milestone produces `.harness/as-built/M<n>.md` from its own diff,
  written by a Cheap-pinned context that is not the orchestrator's.
- The milestone record references the as-built file by path; no orchestrator
  turn reads its contents.
- `harness:as-built` reports a contradiction between what a milestone claimed
  under `### Architecture` and what its diff contains, without issuing a verdict.
- Compose mode produces `drift.md` with the three lists, each entry attributed to
  the milestone that introduced it and reconciled against `## Deviations`.
- The final reviewer raises undeclared divergence as `IMPORTANT` and raises
  nothing for divergence recorded as a deviation.
- A project with no `architecture.md` behaves exactly as before — no as-built
  agent runs, no files are created.

## Never

- Never let the as-built agent edit source, tests, or `architecture.md`. It reads
  the repository and writes one file under `.harness/as-built/`.
- Never let it echo a milestone's claims. Every component and edge it reports is
  derived from files that exist in the diff, or it is not reported.
- Never let a missing or unreadable as-built file block a milestone. The record
  is evidence, not a gate; a failure to draw it is reported and the build
  continues.

# 51. Post-V1 Addition — Ship the Smallest Thing Worth Using

## Problem

The harness takes an agreed scope and builds all of it. `roast-requirements`
resolves ambiguity, `architect` decides structure, and `implement` drives every
requirement to `DONE` through reviewed milestones. Nowhere in that path is there
a place to ask what the *first* useful version is.

§44 already orders milestones by integration risk, so the harness discovers
technical trouble earlier than a layer-by-layer plan would. Ordering is not
scoping: every requirement in `requirements.md` still gets built, and nothing
reaches a user until they all have. On most projects a small part of the scope
carries a real user end to end, and it is worth having long before the rest is
finished.

There is also no route back. A human who trims `requirements.md` by hand to get a
first version out loses the full scope, or keeps it in their head; either way the
question "what did we defer, and when does it come back" has no answer in the
repository.

## Change

A new skill, `harness:scope-mvp`, run after `roast-requirements` (and `architect`
where there is one) and before `implement`.

It carves the agreed scope down to **the smallest implementation that carries one
real user from the system's entry point to a result they actually wanted**, asks
the human whatever the documents cannot answer, and writes three files:

- `.harness/requirements.md` — the MVP scope, in the existing requirements
  template, every deferred reference named under `## Non-Goals`;
- `.harness/architecture.md` — the MVP architecture, in the existing architecture
  template, component ids unchanged from the full design;
- `.harness/mvp.md` — the carve record: the outcome and who gets it, what counts
  as delivered and what does not, the in/deferred tables, any manual steps and
  what automates them, per-component treatment (`IN | STUBBED | DEFERRED`), the
  structural commitments held at full-scope fidelity, and the ordered expansion
  path `E1…En`.

The full documents move unedited to `.harness/full/`.

**Nothing downstream changes.** `implement`, the orchestrator, the reviewer and
`as-built` read the same two paths they always read, and implement an MVP without
knowing it is one. That is the whole reason the MVP occupies the canonical paths
rather than sitting beside them as a fourth document: a scope the harness has to
be taught to recognise is a scope it can also fail to apply.

Four properties are load-bearing.

**End to end and valuable are both required; smallest is the constraint on
them.** The path runs through the real entry point to a real result, and someone
would use that result if nothing more were ever built. Cutting until the path no
longer reaches a result produces something smaller than an MVP and less useful
than either half — and moves the discovery that it is unusable to after it is
built.

**One user, one outcome.** Where the full scope serves several, exactly one is
the MVP. Serving all of them thinly is how a first version ends up neither small
nor usable, and choosing is the work the skill exists to do.

**The skill asks.** Which user comes first, whether it goes to real users or the
team, whether real data is required, where a manual step is acceptable, how much
breadth makes the outcome real — these move requirements between in and deferred
and are not derivable from the documents. Answers are recorded under
`## Decisions` so they are asked once. Anything that changes what the system must
ultimately *do* goes back to `roast-requirements` rather than being absorbed here.

**Scope shrinks; engineering does not.** Tests, correctness of what is in scope,
and the evidence trail are explicitly excluded from what may be cut. The
completion gate would refuse the milestone anyway, and shipping something nobody
can trust to a real user is worse than shipping later.

## Manual steps are scope, not gaps

The smallest useful version often has a person doing something the full system
automates. That is legitimate and it is recorded: `## Manual Steps` names the
step, who performs it, and the increment that automates it. Written down it is a
decision; unwritten it is a hole that surfaces the first time someone uses the
system.

## Two failure modes the carve creates

**Dissolved boundaries.** The shortest path to a running slice is to inline what
the architecture separates. That produces something that works and cannot be
grown, and it is `fixtures/03-drift-undeclared` exactly. The skill states the rule
where the cutting happens: a component may be stubbed or deferred, but a boundary
that survives is crossed rather than dissolved.

**A first version that cannot be grown.** Some decisions are cheap before real
users and real data rest on them and very expensive after — identity and ownership
keys, synchronous versus queued, where the trust boundary sits, the unit of
concurrency. These are taken at full-scope fidelity even where the MVP would not
notice, and recorded. This does not contradict the architect's rule against
designing for hypothetical requirements: it constrains the shape of what is being
built now, and authorises no code for what is not.

## Expansion is informed by use, not by the plan

The expansion order is written before anyone has the system. When an increment is
promoted, what the first users actually needed takes precedence over what the
order predicted, and the reordering is recorded with its reason — that reason is
what building the small version first bought. `.harness/as-built/drift.md`, where
the project has one, is the evidence for whether the MVP built the boundaries the
expansion assumes it can build on.

## Scope

A new `skills/scope-mvp/` (skill plus one template), README, the tier table in
`docs/runtime-contract.md`, and the plugin description. No change to any agent,
to `implement`, to the requirements or architecture templates, or to any fixture.

## Acceptance criteria

- The skill refuses to start on unresolved requirements, a `DRAFT` architecture,
  or a project with any milestone past `TODO`.
- It refuses to carve when the full scope is already minimal, or when nothing
  short of the whole scope is releasable, naming the reason.
- `## Outcome` names one user and one complete outcome through a real entry point,
  and what it replaces.
- Questions asked are limited to ones that move a requirement between in scope and
  deferred; their answers are recorded under `## Decisions`.
- Every full-scope functional requirement appears exactly once across
  `## In Scope` and `## Deferred`; every component appears in `## Components`
  under its original id.
- Every deferred entry names an increment, every increment names at least one
  deferred entry, and every manual step names the increment that automates it.
- `## Value` carries both a `Delivered when` and a `Not delivered if` line, and at
  least one acceptance criterion walks the whole path through the real entry
  point.
- The full documents are present and byte-identical under `.harness/full/` after
  the carve.
- `implement` runs against the carved scope with no change to its own definition.

## Never

- Never write code or scaffolding from the skill. A scope decision is not an
  implementation.
- Never mark the carve `AGREED` without explicit human agreement — the agent does
  not both choose what the product ships without and certify the choice.
- Never cut the path short of the result to make the MVP smaller.
- Never edit the full documents in place; they move once and are read thereafter.
- Never defer tests, in-scope correctness, or evidence to make the MVP smaller.
- Never leave a manual step unrecorded.
- Never build for a deferred increment.
