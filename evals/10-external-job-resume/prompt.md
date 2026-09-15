---
plugins: ["../.."]
runs: 3
max_turns: 80
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Bash, Write, Edit, Agent, Skill]
tags: [runtime-v3, runtime, external-job]
---

Run `/harness:implement-v3` for the current milestone. Inspect the existing
external job's terminal artifact exactly once, do not relaunch or poll it, record
its hash and terminal state, and then resume the milestone. Finish only this
milestone.
