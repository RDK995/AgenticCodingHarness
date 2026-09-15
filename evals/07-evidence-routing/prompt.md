---
plugins: ["../.."]
runs: 3
max_turns: 70
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Bash, Write, Edit, Agent, Skill]
tags: [runtime-v3, routing, economics]
---

Run `/harness:implement-v3` for the current milestone. Treat repository and test
evidence collection as low-risk evidence synthesis with a deterministic oracle;
do not escalate that work to Opus. Finish only this milestone and include the
routing reason in the compact return.
