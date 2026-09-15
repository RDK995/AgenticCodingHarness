---
plugins: ["../.."]
runs: 3
max_turns: 90
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Bash, Write, Edit, Agent, Skill]
tags: [runtime-v3, accuracy, review]
---

Run `/harness:implement-v3` for the current REVIEW milestone. The prior reviewer
was interrupted before creating a terminal result but left a partial. Resume
safely, never credit the partial as a verdict, and finish only this milestone.
