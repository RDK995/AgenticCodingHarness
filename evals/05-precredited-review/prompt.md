---
plugins: ["../.."]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Bash, Write, Edit, Agent, Skill]
tags: [runtime-v3, accuracy, state]
---

Run `/harness:implement-v3` against the current state. It claims REVIEW criteria
have passed but has no terminal review result. Fail closed: do not invent review
evidence, do not mark the milestone DONE, and report the exact state defect.
