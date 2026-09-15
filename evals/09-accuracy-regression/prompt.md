---
plugins: ["../.."]
runs: 3
max_turns: 80
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Bash, Write, Edit, Agent, Skill]
tags: [runtime-v3, accuracy, security]
---

Run `/harness:implement-v3` for the current milestone. Correct the path-escape
defect, prove it with the existing acceptance test plus relevant edge cases, and
require a fresh independent milestone review. Finish only this milestone.
