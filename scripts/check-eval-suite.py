#!/usr/bin/env python3
"""Validate the zero-cost structure and scaffolds of the runtime-v3 eval suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile


EXPECTED_CASES = {
    "01-namespaced-state",
    "02-foreground-workers",
    "03-review-before-terminal",
    "04-review-after-terminal",
    "05-precredited-review",
    "06-hook-denial",
    "07-evidence-routing",
    "08-high-risk-routing",
    "09-accuracy-regression",
    "10-external-job-resume",
}


def check_case(path: Path) -> list[str]:
    errors: list[str] = []
    prompt_path = path / "prompt.md"
    case_path = path / "case.yaml"
    fixture_path = path / "fixture.sh"
    graders = sorted((path / "graders").glob("*.md"))
    try:
        prompt = prompt_path.read_text()
    except OSError as error:
        return [f"{path.name}: cannot read prompt.md: {error}"]
    try:
        case = case_path.read_text()
    except OSError as error:
        errors.append(f"{path.name}: cannot read case.yaml: {error}")
        case = ""
    if not prompt.startswith("---\n") or prompt.count("---") < 2:
        errors.append(f"{path.name}: prompt.md needs YAML frontmatter")
    for marker in (
        'plugins: ["../.."]', "runs: 3", "max_turns:", "timeout_seconds:",
        "allowed_tools:", "tags:", "/harness:implement-v3",
    ):
        if marker not in prompt:
            errors.append(f"{path.name}: prompt.md lacks {marker}")
    if 'schema_version: "1.1"' not in case or "scaffold_script: fixture.sh" not in case:
        errors.append(f"{path.name}: case.yaml is not a schema-1.1 scaffold case")
    if not fixture_path.is_file() or not fixture_path.stat().st_mode & 0o111:
        errors.append(f"{path.name}: fixture.sh must exist and be executable")
    if len(graders) < 2:
        errors.append(f"{path.name}: needs at least two deterministic graders")
    grader_text = "\n".join(grader.read_text() for grader in graders)
    if "type: llm" in grader_text or "type: baseline" in grader_text:
        errors.append(f"{path.name}: zero-cost suite must not contain model graders")
    if "type: tool_used" not in grader_text:
        errors.append(f"{path.name}: needs a process/tool grader")
    if not re.search(r"type: (?:regex|file_exists)", grader_text):
        errors.append(f"{path.name}: needs a deterministic outcome grader")
    return errors


def check_scaffold(path: Path) -> list[str]:
    with tempfile.TemporaryDirectory() as directory:
        completed = subprocess.run(
            [str(path / "fixture.sh")], cwd=directory, text=True,
            capture_output=True, check=False,
        )
        if completed.returncode:
            return [f"{path.name}: scaffold failed: {completed.stderr.strip()}"]
        root = Path(directory)
        required = [
            root / ".git", root / ".harness" / "state.json",
            root / ".harness" / "requirements.md",
            root / ".harness" / "milestones.md",
        ]
        missing = [str(item.relative_to(root)) for item in required if not item.exists()]
        if missing:
            return [f"{path.name}: scaffold omitted {', '.join(missing)}"]
        try:
            state = json.loads((root / ".harness" / "state.json").read_text())
        except (OSError, json.JSONDecodeError) as error:
            return [f"{path.name}: scaffold state is invalid JSON: {error}"]
        if state.get("schema_version") != 2:
            return [f"{path.name}: scaffold state must use schema version 2"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--eval-dir", type=Path,
        default=Path(__file__).resolve().parents[1] / "evals",
    )
    parser.add_argument("--skip-scaffolds", action="store_true")
    args = parser.parse_args()
    cases = {path.name: path for path in args.eval_dir.iterdir() if path.name[:2].isdigit()}
    errors: list[str] = []
    missing = sorted(EXPECTED_CASES - set(cases))
    extra = sorted(set(cases) - EXPECTED_CASES)
    if missing:
        errors.append("missing eval cases: " + ", ".join(missing))
    if extra:
        errors.append("unexpected numbered eval cases: " + ", ".join(extra))
    for name in sorted(EXPECTED_CASES & set(cases)):
        errors.extend(check_case(cases[name]))
        if not args.skip_scaffolds:
            errors.extend(check_scaffold(cases[name]))
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print(f"PASS {len(cases)} native plugin-eval cases and scaffolds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
