---
name: implement-loop
description: Runs /harness:implement over and over, each time in a brand-new headless session, so milestones are worked through unattended without the human having to /clear and re-invoke between them. Stops on all DONE, a BLOCKED milestone, an iteration that changed nothing, --until <milestone>, --max <n>, or an error. Use when the user asks to loop through the milestones, implement and clear in a loop, run all milestones unattended, or keep going through the milestones without them.
---

Automate the `/clear`-and-re-invoke step that `/harness:implement` asks the human
for at every milestone boundary. A fresh `claude -p` process **is** the `/clear`:
the script below starts one per iteration, and decides whether to start another
from `.harness/state.json` and `git rev-parse HEAD` alone — never from what a
session said.

This session is a launcher and a reporter. It does no implementation, review or
milestone work, reads no requirements, milestones or diffs, and never edits
`.harness/`. Every rule of `/harness:implement` — one phase per invocation,
reviewer independence, the two-cycle cap, never push, never merge, never skip a
`BLOCKED` milestone — is enforced by each inner `/harness:implement` session,
because each one *is* that skill, run fresh.

## Steps

```
1. IF .harness/state.json does not exist:
       STOP — tell the user to run /harness:implement once interactively
       first. That run plans the milestones and may need to ask them things a
       headless session cannot.

2. Run, and STOP on any error it reports:
       python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-state.py .harness/state.json
       --milestones .harness/milestones.md --requirements .harness/requirements.md

3. Run in the BACKGROUND (Bash run_in_background), from the project root,
   passing through only the arguments the user gave (--until, --max,
   --permission-mode):
       python3 ${CLAUDE_PLUGIN_ROOT}/scripts/implement-loop.py
       --plugin-dir ${CLAUDE_PLUGIN_ROOT} [user args]
   --plugin-dir makes every inner session load this same harness.
   Tell the user it is running, and roughly how to stop it (stop the
   background task; the milestone in flight resumes from state next time).

4. Wait for the completion notification. Do not poll, do not sleep, and do
   not read .harness/evidence/implement-loop/*.log into context — each is a
   whole session's transcript, and reading them is what the fresh sessions
   exist to avoid. Read only the script's own stdout.

5. When it exits, report in plain words:
       - each summary line: which milestone, what its status went from and
         to, and whether a commit was made;
       - why it stopped, and what the user should do next (see the table);
       - the log directory, for them to open if they want detail.
   Then STOP. Do not re-run the loop, and do not continue the work yourself.
```

| Exit | Meaning | What to tell the user |
| --- | --- | --- |
| 0 | Every milestone is `DONE` | Done; the last session's log has the final report. Nothing was pushed or merged. |
| 3, `BLOCKED` | A milestone needs a human decision | Open `.harness/milestones.md` for that milestone's escalation, decide, then re-run. |
| 3, no progress | A session changed neither state nor `HEAD` | Usually a permission was denied, or the milestone is waiting on something only a person can do (e.g. a live check). The newest log says which. |
| 3, `--until` / `--max` | The limit the user set was reached | Re-run to continue. |
| 3, other status | The next milestone has a status `/harness:implement` has no step for (e.g. `DEFERRED`) | That needs the user's decision. |
| 1 | A session exited with an error, or state could not be read | Point them at the named log. |

## Permissions

A headless session cannot answer a permission prompt. The script passes
`--permission-prompts none`, so anything that would have prompted is **denied**
rather than left waiting — a denied step then shows up as an iteration that made
no progress, and the loop stops.

The default `--permission-mode` is `acceptEdits`: file edits inside the project
are allowed, and every Bash command must already be allowed by the project's
settings. Before running unattended, the user needs an allowlist in the project's
`.claude/settings.json` covering what the harness runs — at least `git`
(`add`, `commit`, `checkout -b`, `rev-parse`, `diff`, `log`, `status`),
`python3` for the harness's own scripts, and the project's test, lint and build
commands. `Read`, `Grep`, `Glob` and subagents need no entry.

`bypassPermissions` removes every check, including the ones that stop a
confused session from running something destructive, for as long as the loop
runs and with no one watching. Pass it only when the user explicitly asks, and
only in a disposable environment (a container or VM with nothing to lose and no
credentials worth taking). Never choose it on their behalf to make a stalled loop
progress — stalling on a denied command is the safety working.

## Never

- Never do milestone work in this session, or read requirements, milestones,
  reviews or diffs to "help". If the loop stops, report and hand back.
- Never pass `--permission-mode bypassPermissions` unless the user asked for it
  in this conversation.
- Never read the per-iteration logs into context.
- Never push, merge, or open a pull request.
