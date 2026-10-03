---
name: implement-loop
description: Runs /harness:implement over and over, each time in a brand-new background session the user can watch with `claude attach`, so milestones are worked through unattended without the human having to /clear and re-invoke between them. Stops on all DONE, a milestone whose task plan is not yet agreed, a BLOCKED milestone, an iteration that changed nothing, --until <milestone>, --max <n>, or an error. Use when the user asks to loop through the milestones, implement and clear in a loop, run all milestones unattended, or keep going through the milestones without them.
---

Automate the `/clear`-and-re-invoke step that `/harness:implement` asks the human
for at every milestone boundary. A fresh session **is** the `/clear`: the script
below starts one per iteration as an ordinary background session
(`claude --bg`), and decides whether to start another from `.harness/state.json`
and `git rev-parse HEAD` alone — never from what a session said.

Each session looks exactly like a normal one: `claude attach <id>` opens it in a
terminal, live, and ← leaves it running. `claude agents` lists them all. Unlike
other background sessions they work in the project's checkout itself, not a
worktree, since the state and milestone branches live there.

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
       first. That run plans the milestones and may need to ask them things
       before any loop starts.

2. Run, and STOP on any error it reports:
       python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-state.py .harness/state.json
       --milestones .harness/milestones.md --requirements .harness/requirements.md

3. Start the loop DETACHED, from the project root, passing through only the
   arguments the user gave (--until, --max, --permission-mode). It must not
   be a Bash background task: those are killed after at most two hours, and
   a loop waiting on the user can run far longer.
       mkdir -p .harness/evidence/implement-loop
       f=.harness/evidence/implement-loop/loop-$(date -u +%Y%m%dT%H%M%SZ)-$$.log
       nohup python3 -u ${CLAUDE_PLUGIN_ROOT}/scripts/implement-loop.py
         --plugin-dir ${CLAUDE_PLUGIN_ROOT} [user args] > "$f" 2>&1 &
       echo "$! $f"
   --plugin-dir makes every inner session load this same harness. Note the
   printed PID and log path; each launch gets its own log, so a second launch
   never overwrites a running loop's. Only one loop runs per checkout: a
   second exits at once with "already running", and that is the line to
   report. Tell the user it is running; that each milestone's session
   can be watched live with `claude attach <id>` (the id arrives in the next
   step); and how to stop it: `kill <PID>`, then `claude stop <id>` for the
   session in flight — the milestone resumes from state next time.

4. Stream the loop's lines into this conversation with the Monitor tool,
   timeout_ms 1800000 (the maximum), description "implement-loop progress":
       f=<LOG>; n=<N>; pid=<PID>
       while :; do
         t=$(wc -l < "$f"); [ "$t" -gt "$n" ] && sed -n "$((n+1)),${t}p" "$f" && n=$t
         kill -0 "$pid" 2>/dev/null || { sed -n "$((n+1)),\$p" "$f"; exit 0; }
         sleep 5
       done
   N is 0 the first time. If the monitor expires while the PID is still
   alive, re-arm it with N set to the current `wc -l` of the log.
   Relay each line as it arrives, in plain words:
       - "started -- watch it: claude attach <id>": which milestone is
         running and the command to watch it;
       - "is waiting for you (permission prompt)": the session has paused on
         a question only the user can answer; give them the attach command.
         It waits as long as it takes. Also send a PushNotification, since
         they may not be looking;
       - a "[n] M: A -> B, HEAD x -> y" line: the milestone moved from A to B,
         and whether a commit was made.
   Do not poll or sleep otherwise. Read only this launch's log, never a session's
   transcript or `claude logs` output — reading them is what the fresh
   sessions exist to avoid.

5. When the monitor exits, read the last line of the log (STOP: ...) and
   report in plain words why it stopped and what the user should do next
   (see the table).
   Then STOP. Do not re-run the loop, and do not continue the work yourself.
```

| `STOP:` line | Meaning | What to tell the user |
| --- | --- | --- |
| all milestones are DONE and the all-DONE check passed | Every milestone is `DONE`, and the loop ran the final session in which implement checks that and writes its report | Done; `claude attach` on the "final report" session shows the report. Nothing was pushed or merged. |
| every milestone is DONE but the all-DONE check failed | The milestones say DONE, but the final check rejects the state | Pass on the reasons; the final-report session explains them. Not finished. |
| another implement-loop … is already running | A loop is already working in this checkout | Nothing was started. Watch or stop the running one. |
| … needs its task plan agreed | The next milestone has not been planned, or its plan is still a draft | Run `/harness:plan-milestone`, agree the plan, then run the loop again. |
| … is BLOCKED | A milestone needs a human decision | Open `.harness/milestones.md` for that milestone's escalation, decide, then re-run. |
| changed neither … nor HEAD | A session finished without moving anything | The milestone is waiting on something only a person can do (e.g. a live check), or a permission was refused. The line gives the `claude attach` command that shows which. |
| reached --until / --max | The limit the user set was reached | Re-run to continue. |
| has status … no step for | The next milestone has a status `/harness:implement` has no step for (e.g. `DEFERRED`) | That needs the user's decision. |
| could not start / stopped before it finished / disappeared / cannot read | A session failed to start or ended early, or state could not be read | Pass on the line. If they stopped the session themselves, re-running resumes. |

## Permissions

A permission prompt in a loop session behaves as it does in any session: it
**waits** for the user, who attaches and answers it. The loop reports the wait
once and keeps waiting, however long that takes; nothing is denied on their
behalf.

The default `--permission-mode` is `acceptEdits`: file edits inside the project
are allowed, and every other Bash command prompts unless the project's settings
allow it. To be asked less, the user can add an allowlist to the project's
`.claude/settings.json` covering what the harness runs — `git` (`add`,
`commit`, `checkout -b`, `rev-parse`, `diff`, `log`, `status`), `python3` for
the harness's own scripts, and the project's test, lint and build commands.

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
- Never read a session's transcript or `claude logs` output into context;
  this launch's log is the only thing to read.
- Never answer a session's permission prompt for the user, or attach to one.
- Never push, merge, or open a pull request.
