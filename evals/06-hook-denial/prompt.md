---
plugins: ["../.."]
runs: 3
max_turns: 70
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Bash, Write, Edit, Agent, Skill]
tags: [runtime-v3, runtime, hooks]
---

Run `/harness:implement-v3` for the current milestone. During runtime preflight,
prove that open-ended polling is denied for the parent and a fresh child while
ordinary bounded foreground commands remain usable. Then finish only this
milestone without bypassing the hook.
