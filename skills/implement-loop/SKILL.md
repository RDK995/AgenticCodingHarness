---
name: implement-loop
description: Start, check on, or stop the unattended background loop that runs /harness:implement milestone after milestone. Use when the user wants the harness to keep implementing in the background, or asks for the status of or to stop that loop.
---

Control the background implementation loop by running exactly one command
from the project directory. Choose it from what the user asked:

- User asks to start the loop: `start`
- User asks to stop the loop: `stop`
- User asks how it is going, or the request is unclear: `status`

Commands (run one only):

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/implement-loop.py" start
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/implement-loop.py" status
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/implement-loop.py" stop
```

Report the command's output back to the user plainly.

`start` returns immediately. A detached driver keeps working in the background
after it returns, so do not wait for the loop to finish and do not poll it.

Do not run `/harness:implement` yourself. The driver runs it for each milestone.
Do not do any milestone work in this session.
