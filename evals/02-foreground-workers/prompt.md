---
plugins: ["../.."]
runs: 3
max_turns: 90
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Bash, Write, Edit, Agent, Skill]
tags: [runtime-v3, runtime, foreground]
---

Run `/harness:implement-v3` for the current milestone. Its two independent
acceptance criteria should be dispatched concurrently in the same tool-use turn.
Use foreground returns only and finish only this milestone.
