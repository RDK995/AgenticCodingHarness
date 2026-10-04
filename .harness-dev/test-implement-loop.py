#!/usr/bin/env python3
"""Black-box tests for the implement-loop stop conditions.

A fake `claude` on PATH stands in for the background sessions. `claude --bg`
takes the next scripted step: set milestone statuses in .harness/state.json,
optionally commit, and register a session that `claude agents --json` then
reports -- done at once, or after waiting on a permission prompt for a few
polls. A step may also take up the waiting answer (recording what it read and
deleting answer.md and question.md, as the implement skill does) and may ask a
question by writing question.md. `claude stop` marks it stopped.

The loop runs as a copy beside a stand-in check-state.py, whose --all-done gate
passes only when every milestone is DONE and current_milestone is null, and
which records how it was called.
"""

import fcntl
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "scripts" / "implement-loop.py"

FAKE_CLAUDE = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json, os, subprocess, sys
    from pathlib import Path
    args = sys.argv[1:]
    sessions_path = Path(os.environ["FAKE_CLAUDE_SESSIONS"])
    sessions = json.loads(sessions_path.read_text()) if sessions_path.exists() else []
    def save():
        sessions_path.write_text(json.dumps(sessions))
    if args[:1] == ["agents"]:
        listed = [{"name": "an unrelated interactive session", "status": "busy"}]
        for session in sessions:
            if session.get("polls", 0) > 0:
                session["polls"] -= 1
                if session["polls"] == 0:
                    session.update(status="idle", state=session.pop("then"))
                    session.pop("waitingFor", None)
            if not session.get("gone"):
                listed.append({k: v for k, v in session.items() if k not in ("polls", "then", "vanish")})
            if session.get("vanish") and session.get("polls", 0) == 0:
                session["gone"] = True
        save()
        print(json.dumps(listed))
        sys.exit(0)
    if args[:1] == ["stop"]:
        with Path(os.environ["FAKE_CLAUDE_STOPS"]).open("a") as handle:
            handle.write(args[1] + "\\n")
        for session in sessions:
            if session["id"] == args[1]:
                session["state"] = "stopped"
        save()
        sys.exit(0)
    assert args[0] == "--bg", args
    with Path(os.environ["FAKE_CLAUDE_CALLS"]).open("a") as handle:
        handle.write(json.dumps(args) + "\\n")
    script = Path(os.environ["FAKE_CLAUDE_SCRIPT"])
    steps = json.loads(script.read_text())
    step = steps.pop(0) if steps else {}
    script.write_text(json.dumps(steps))
    if step.get("exit"):
        print("could not start")
        sys.exit(step["exit"])
    state_path = Path(".harness/state.json")
    if step.get("set"):
        state = json.loads(state_path.read_text())
        for milestone, status in step["set"].items():
            state["milestones"].setdefault(milestone, {})["status"] = status
        state_path.write_text(json.dumps(state, indent=2))
    exchange = Path(".harness/evidence/implement-loop")
    if step.get("take_answer"):
        with Path(os.environ["FAKE_CLAUDE_ANSWERS"]).open("a") as handle:
            handle.write((exchange / "answer.md").read_text())
        (exchange / "answer.md").unlink()
        (exchange / "question.md").unlink()
    if step.get("ask"):
        (exchange / "question.md").write_text(step["ask"])
    if step.get("commit"):
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-qm", "fake step", "--allow-empty"], check=True)
    session = {
        "id": f"s{len(sessions) + 1}",
        "name": args[args.index("--name") + 1],
        "kind": "background",
        "startedAt": len(sessions) + 1,
        "status": "idle",
        "state": "done",
    }
    if step.get("wait"):
        session.update(status="waiting", waitingFor="permission prompt", state="blocked",
                       polls=step["wait"], then="done")
        if "reason" in step and step["reason"] is None:
            session.update(status="idle")
            del session["waitingFor"]
    if step.get("end") in ("stopped", "vanish"):
        session.update(status="busy", state="working", polls=1, then="stopped")
        if step["end"] == "vanish":
            session.update(then="working", vanish=True)
    sessions.append(session)
    save()
    print(f"backgrounded · {session['id']} · {session['name']}")
    """
)

FAKE_CHECK_STATE = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json, os, sys
    from pathlib import Path
    Path(os.environ["FAKE_CHECK_CALLS"]).open("a").write(json.dumps(sys.argv[1:]) + "\\n")
    state = json.loads(Path(sys.argv[1]).read_text())
    if state["current_milestone"] is not None:
        print("ERROR: all-DONE check requires current_milestone to be null", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
    """
)


class ImplementLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.project = base / "project"
        (self.project / ".harness").mkdir(parents=True)
        self.bin = base / "bin"
        self.bin.mkdir()
        fake = self.bin / "claude"
        fake.write_text(FAKE_CLAUDE)
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        self.script = base / "steps.json"
        self.calls = base / "calls.jsonl"
        self.sessions = base / "sessions.json"
        self.stops = base / "stops.txt"
        self.checks = base / "checks.jsonl"
        self.answers = base / "answers.txt"
        scripts = base / "scripts"
        scripts.mkdir()
        self.loop = scripts / "implement-loop.py"
        shutil.copy(LOOP, self.loop)
        (scripts / "check-state.py").write_text(FAKE_CHECK_STATE)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "test")

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.project, check=True, text=True, capture_output=True
        ).stdout.strip()

    def seed(self, statuses, current=None, plans=None):
        # Every milestone carries an agreed plan unless `plans` says otherwise;
        # a plan of None means the milestone has never been planned.
        plans = plans or {}
        milestones = {}
        for key, value in statuses.items():
            plan = plans.get(key, "AGREED")
            milestones[key] = {"status": value}
            if plan is not None:
                milestones[key]["plan"] = {"status": plan, "artifact": f".harness/plans/{key}.md"}
        state = {
            "schema_version": 1,
            "current_milestone": current,
            "milestones": milestones,
        }
        (self.project / ".harness" / "state.json").write_text(json.dumps(state, indent=2))
        self.git("add", "-A")
        self.git("commit", "-qm", "baseline")

    def run_loop(self, steps, *args):
        self.script.write_text(json.dumps(steps))
        env = {
            **os.environ,
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "FAKE_CLAUDE_SCRIPT": str(self.script),
            "FAKE_CLAUDE_CALLS": str(self.calls),
            "FAKE_CLAUDE_SESSIONS": str(self.sessions),
            "FAKE_CLAUDE_STOPS": str(self.stops),
            "FAKE_CHECK_CALLS": str(self.checks),
            "FAKE_CLAUDE_ANSWERS": str(self.answers),
            "HARNESS_LOOP_POLL_SECONDS": "0.01",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        return subprocess.run(
            [sys.executable, str(self.loop), *args],
            cwd=self.project,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def call_count(self):
        return len(self.calls.read_text().splitlines()) if self.calls.exists() else 0

    def statuses(self):
        state = json.loads((self.project / ".harness" / "state.json").read_text())
        return {key: value["status"] for key, value in state["milestones"].items()}

    def test_runs_until_every_milestone_is_done(self):
        self.seed({"M1": "TODO", "M2": "TODO"})
        completed = self.run_loop(
            [
                {"set": {"M1": "REVIEW"}, "commit": True},
                {"set": {"M1": "DONE"}, "commit": True},
                {"set": {"M2": "DONE"}, "commit": True},
            ]
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        # Three milestone sessions, then the one that writes the final report.
        self.assertEqual(self.call_count(), 4)
        lines = completed.stdout.splitlines()
        self.assertEqual(lines[0], "[1] M1 (TODO) started -- watch it: claude attach s1")
        self.assertIn("[1] M1: TODO -> REVIEW, HEAD ", lines[1])
        self.assertIn("(session s1)", lines[1])
        self.assertIn("[2] M1: REVIEW -> DONE", lines[3])
        self.assertIn("[3] M2: TODO -> DONE", lines[5])
        self.assertIn("[4] final report written (session s4)", lines)
        self.assertEqual(lines[-1], "STOP: all milestones are DONE and the all-DONE check passed")
        # Each finished session is stopped, which keeps its conversation.
        self.assertEqual(self.stops.read_text().split(), ["s1", "s2", "s3", "s4"])
        gate = json.loads(self.checks.read_text().splitlines()[-1])
        self.assertEqual(
            gate,
            [
                str(self.project.resolve() / ".harness/state.json"),
                "--milestones",
                str(self.project.resolve() / ".harness/milestones.md"),
                "--requirements",
                str(self.project.resolve() / ".harness/requirements.md"),
                "--all-done",
            ],
        )

    def test_unplanned_todo_milestone_stops_before_any_session(self):
        self.seed({"M1": "TODO"}, plans={"M1": None})
        completed = self.run_loop([{"set": {"M1": "REVIEW"}, "commit": True}])
        self.assertEqual(completed.returncode, 3, completed.stdout + completed.stderr)
        self.assertEqual(self.call_count(), 0)
        self.assertEqual(
            completed.stdout.splitlines()[-1],
            "STOP: M1 needs its task plan agreed: run /harness:plan, then the loop again",
        )

    def test_draft_plan_is_not_agreed(self):
        self.seed({"M1": "TODO"}, plans={"M1": "DRAFT"})
        completed = self.run_loop([{"set": {"M1": "REVIEW"}, "commit": True}])
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 0)
        self.assertIn("M1 needs its task plan agreed", completed.stdout)

    def test_stops_at_the_next_milestone_that_needs_a_plan(self):
        self.seed({"M1": "TODO", "M2": "TODO"}, plans={"M2": None})
        completed = self.run_loop(
            [
                {"set": {"M1": "REVIEW"}, "commit": True},
                {"set": {"M1": "DONE"}, "commit": True},
                {"set": {"M2": "DONE"}, "commit": True},
            ]
        )
        self.assertEqual(completed.returncode, 3, completed.stdout + completed.stderr)
        self.assertEqual(self.call_count(), 2)
        self.assertEqual(self.statuses(), {"M1": "DONE", "M2": "TODO"})
        self.assertIn("M2 needs its task plan agreed", completed.stdout.splitlines()[-1])

    def test_in_progress_milestone_from_an_older_harness_runs_without_a_plan(self):
        self.seed({"M1": "IN_PROGRESS"}, plans={"M1": None})
        completed = self.run_loop([{"set": {"M1": "DONE"}, "commit": True}])
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(self.statuses(), {"M1": "DONE"})

    def test_already_done_runs_only_the_final_report(self):
        self.seed({"M1": "DONE"})
        completed = self.run_loop([])
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(self.call_count(), 1)
        self.assertRegex(json.loads(self.calls.read_text())[2], r"^implement-loop final #1 ")

    def test_failed_all_done_gate_is_an_error(self):
        self.seed({"M1": "DONE"}, current="M1")
        completed = self.run_loop([])
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.call_count(), 1)
        self.assertIn(
            "STOP: every milestone is DONE but the all-DONE check failed: "
            "all-DONE check requires current_milestone to be null",
            completed.stdout,
        )

    def test_final_report_is_not_counted_against_max(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([{"set": {"M1": "DONE"}, "commit": True}], "--max", "1")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(self.call_count(), 2)

    def test_final_report_session_that_reopens_a_milestone_continues_the_loop(self):
        self.seed({"M1": "DONE"})
        completed = self.run_loop([{"set": {"M1": "REVIEW"}}, {"set": {"M1": "DONE"}, "commit": True}])
        self.assertEqual(completed.returncode, 0, completed.stdout)
        # Final report reopened M1; M1 ran; the gate passed without a second report.
        self.assertEqual(self.call_count(), 2)

    def test_second_loop_in_the_same_checkout_refuses_to_start(self):
        self.seed({"M1": "TODO"})
        lock_path = self.project / ".harness/evidence/implement-loop/.lock"
        lock_path.parent.mkdir(parents=True)
        with lock_path.open("a+") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            held.write("4242\n")
            held.flush()
            completed = self.run_loop([{"set": {"M1": "DONE"}}])
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.call_count(), 0)
        self.assertIn("another implement-loop (pid 4242) is already running in this checkout", completed.stdout)
        # Once the first loop is gone, the checkout is free again.
        completed = self.run_loop([{"set": {"M1": "DONE"}, "commit": True}])
        self.assertEqual(completed.returncode, 0, completed.stdout)

    def test_stops_when_selected_milestone_becomes_blocked(self):
        self.seed({"M1": "TODO", "M2": "TODO"})
        completed = self.run_loop([{"set": {"M1": "BLOCKED"}, "commit": True}])
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 1)
        self.assertIn("M1 is BLOCKED", completed.stdout)

    def test_blocked_before_start_runs_nothing_and_never_skips_ahead(self):
        self.seed({"M1": "DONE", "M2": "BLOCKED", "M3": "TODO"})
        completed = self.run_loop([])
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 0)
        self.assertIn("M2 is BLOCKED", completed.stdout)

    def test_status_without_an_implement_step_stops(self):
        self.seed({"M1": "DEFERRED", "M2": "TODO"})
        completed = self.run_loop([])
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 0)
        self.assertIn("DEFERRED", completed.stdout)

    def test_no_progress_stops(self):
        self.seed({"M1": "REVIEW"})
        completed = self.run_loop([{"say": "waiting for a human live check"}, {}])
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 1)
        self.assertIn("changed neither", completed.stdout)

    def test_state_change_without_commit_counts_as_progress(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([{"set": {"M1": "IN_PROGRESS"}}, {"set": {"M1": "DONE"}}])
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(self.call_count(), 3)  # two steps, then the final report

    def test_commit_without_state_change_counts_as_progress(self):
        self.seed({"M1": "IN_PROGRESS"})
        completed = self.run_loop([{"commit": True}, {"set": {"M1": "DONE"}}])
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(self.call_count(), 3)  # two steps, then the final report

    def test_until_stops_before_running_that_milestone(self):
        self.seed({"M1": "TODO", "M2": "TODO", "M3": "TODO"})
        completed = self.run_loop(
            [{"set": {"M1": "DONE"}, "commit": True}, {"set": {"M2": "DONE"}}], "--until", "M2"
        )
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 1)
        self.assertEqual(self.statuses()["M2"], "TODO")
        self.assertIn("reached --until M2", completed.stdout)

    def test_until_rejects_unknown_or_done_milestone(self):
        self.seed({"M1": "DONE", "M2": "TODO"})
        for target in ("M9", "M1"):
            with self.subTest(target=target):
                completed = self.run_loop([], "--until", target)
                self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.call_count(), 0)

    def test_max_iterations(self):
        self.seed({"M1": "TODO", "M2": "TODO", "M3": "TODO"})
        completed = self.run_loop(
            [{"set": {"M1": "DONE"}, "commit": True}, {"set": {"M2": "DONE"}, "commit": True}],
            "--max",
            "2",
        )
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(self.call_count(), 2)
        self.assertIn("reached --max 2", completed.stdout)

    def test_nonzero_claude_exit_is_an_error(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([{"exit": 7}])
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.call_count(), 1)
        self.assertIn("exited with status 7: could not start", completed.stdout)

    def test_waits_for_a_permission_prompt_and_says_so_once(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([{"set": {"M1": "DONE"}, "commit": True, "wait": 5}])
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        waiting = [line for line in completed.stdout.splitlines() if "waiting for you" in line]
        self.assertEqual(waiting, ["[1] M1 (TODO) is waiting for you (permission prompt) -- claude attach s1"])

    def test_reports_a_session_blocked_on_input_without_a_named_reason(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([{"set": {"M1": "DONE"}, "commit": True, "wait": 3, "reason": None}])
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("[1] M1 (TODO) is waiting for you (your input) -- claude attach s1", completed.stdout)

    def test_session_stopped_before_finishing_is_an_error(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([{"set": {"M1": "IN_PROGRESS"}, "end": "stopped"}])
        self.assertEqual(completed.returncode, 1)
        self.assertIn("session s1 was stopped before it finished", completed.stdout)

    def test_session_that_disappears_is_an_error(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([{"set": {"M1": "IN_PROGRESS"}, "end": "vanish"}])
        self.assertEqual(completed.returncode, 1)
        self.assertIn("session s1 disappeared before it finished", completed.stdout)

    def test_log_dir_is_kept_out_of_git(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([{"set": {"M1": "DONE"}, "commit": True}])
        self.assertEqual(completed.returncode, 0)
        log = self.project / ".harness/evidence/implement-loop/loop.log"
        log.write_text("loop output written by the launcher skill\n")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_starts_a_named_background_session_with_safe_default_permission_mode(self):
        self.seed({"M1": "TODO"})
        self.run_loop([{"set": {"M1": "DONE"}}], "--plugin-dir", "/plugins/harness")
        argv = json.loads(self.calls.read_text().splitlines()[0])
        self.assertEqual(argv[0], "--bg")
        # Told it is unattended, so it writes questions down instead of waiting.
        self.assertEqual(argv[-1], "/harness:implement unattended")
        self.assertRegex(argv[argv.index("--name") + 1], r"^implement-loop M1 #1 \d{8}T\d{6}Z \d+$")
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "acceptEdits")
        # Works in this checkout, where the loop reads state and HEAD.
        self.assertEqual(json.loads(argv[argv.index("--settings") + 1]), {"worktree": {"bgIsolation": "none"}})
        # Prompts wait for the human in the attached session; they are not auto-denied.
        self.assertNotIn("--permission-prompts", argv)
        self.assertNotIn("-p", argv)
        self.assertEqual(argv[argv.index("--plugin-dir") + 1], "/plugins/harness")
        self.assertNotIn("--dangerously-skip-permissions", argv)

    def test_permission_mode_passthrough(self):
        self.seed({"M1": "TODO"})
        self.run_loop([{"set": {"M1": "DONE"}}], "--permission-mode", "dontAsk")
        argv = json.loads(self.calls.read_text().splitlines()[0])
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "dontAsk")

    def answer_file(self, text):
        path = Path(self.temp.name) / "reply.txt"
        path.write_text(text)
        return path

    def question(self):
        return self.project / ".harness/evidence/implement-loop/question.md"

    def test_a_question_stops_the_loop_and_is_printed(self):
        self.seed({"M1": "TODO", "M2": "TODO"})
        completed = self.run_loop(
            [{"set": {"M1": "BLOCKED"}, "commit": True, "ask": "M1 is blocked.\nRetry the review, or stop?\n"}]
        )
        self.assertEqual(completed.returncode, 4, completed.stdout + completed.stderr)
        self.assertEqual(self.call_count(), 1)
        lines = completed.stdout.splitlines()
        self.assertIn("[1] M1: TODO -> BLOCKED", lines[1])
        self.assertEqual(
            lines[2:5],
            ["QUESTION -- the loop needs your answer:", "  | M1 is blocked.", "  | Retry the review, or stop?"],
        )
        self.assertEqual(
            lines[-1], "STOP: a session asked you a question; answer it and re-run with --answer-file"
        )

    def test_an_unanswered_question_is_shown_again_and_nothing_runs(self):
        self.seed({"M1": "TODO"})
        self.question().parent.mkdir(parents=True, exist_ok=True)
        self.question().write_text("Which way?\n")
        completed = self.run_loop([{"set": {"M1": "DONE"}}])
        self.assertEqual(completed.returncode, 4)
        self.assertEqual(self.call_count(), 0)
        self.assertIn("  | Which way?", completed.stdout)

    def test_answer_reaches_a_session_even_for_a_blocked_milestone_then_the_loop_carries_on(self):
        self.seed({"M1": "BLOCKED"})
        self.question().parent.mkdir(parents=True, exist_ok=True)
        self.question().write_text("Retry the review, or stop?\n")
        completed = self.run_loop(
            [{"take_answer": True, "set": {"M1": "REVIEW"}, "commit": True}, {"set": {"M1": "DONE"}, "commit": True}],
            "--answer-file",
            self.answer_file("Retry it once more.\n"),
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(self.answers.read_text(), "Retry it once more.\n")
        self.assertIn("[1] M1: BLOCKED -> REVIEW", completed.stdout)
        self.assertFalse(self.question().exists())

    def test_answer_left_unread_is_an_error(self):
        self.seed({"M1": "BLOCKED"})
        self.question().parent.mkdir(parents=True, exist_ok=True)
        self.question().write_text("Retry?\n")
        completed = self.run_loop([{"set": {"M1": "REVIEW"}}], "--answer-file", self.answer_file("Yes.\n"))
        self.assertEqual(completed.returncode, 1)
        self.assertIn("did not take up the answer", completed.stdout)

    def test_a_follow_up_question_after_an_answer_stops_again(self):
        self.seed({"M1": "BLOCKED"})
        self.question().parent.mkdir(parents=True, exist_ok=True)
        self.question().write_text("Retry?\n")
        completed = self.run_loop(
            [{"take_answer": True, "ask": "Retry with which reviewer tier?\n"}],
            "--answer-file",
            self.answer_file("Yes.\n"),
        )
        self.assertEqual(completed.returncode, 4)
        self.assertIn("  | Retry with which reviewer tier?", completed.stdout)

    def test_answer_without_a_waiting_question_is_an_error(self):
        self.seed({"M1": "TODO"})
        completed = self.run_loop([], "--answer-file", self.answer_file("Yes.\n"))
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.call_count(), 0)
        self.assertIn("no question is waiting", completed.stdout)

    def test_missing_state_is_an_error(self):
        completed = self.run_loop([])
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.call_count(), 0)


if __name__ == "__main__":
    unittest.main()
