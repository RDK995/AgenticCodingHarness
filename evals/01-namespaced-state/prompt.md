---
plugins: ["../.."]
runs: 3
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Bash, Write, Edit, Agent, Skill]
tags: [runtime-v3, accuracy, state]
---

Run `/harness:implement-v3` for the current milestone. Preserve the opaque
`P2-R10.19` and `P2-M7c` identifiers exactly, finish only that milestone, and
report the terminal state and evidence paths.
