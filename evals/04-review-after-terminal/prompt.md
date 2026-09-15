---
plugins: ["../.."]
runs: 3
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Bash, Write, Edit, Agent, Skill]
tags: [runtime-v3, accuracy, review]
---

Run `/harness:implement-v3` for the current REVIEW milestone. A prior reviewer
completed the authoritative same-HEAD terminal result before its response was
cut off. Consume that valid artifact without repeating the review and finish only
this milestone.
