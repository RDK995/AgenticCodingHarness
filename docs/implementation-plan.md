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