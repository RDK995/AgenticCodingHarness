#!/usr/bin/env python3
"""Materialize comparable control or treatment plugin-eval cases without running them."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


DEFAULT_CASES = (
    "01-namespaced-state",
    "07-evidence-routing",
    "08-high-risk-routing",
    "09-accuracy-regression",
)


def copy_arm(root: Path, arm: str, case_names: list[str]) -> Path:
    source = root / "evals"
    destination = root / f"evals-{arm}"
    if destination.exists():
        raise ValueError(
            f"{destination} already exists; remove the generated directory explicitly before rebuilding"
        )
    destination.mkdir()
    shutil.copytree(source / "_support", destination / "_support")
    for name in case_names:
        case_source = source / name
        if not case_source.is_dir():
            raise ValueError(f"unknown eval case {name}")
        case_destination = destination / name
        shutil.copytree(case_source, case_destination)
        if arm == "control":
            for path in case_destination.rglob("*.md"):
                path.write_text(path.read_text().replace("implement-v3", "implement"))
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True, choices=("control", "treatment"))
    parser.add_argument("--case", action="append", dest="cases", choices=sorted(DEFAULT_CASES))
    parser.add_argument(
        "--plugin-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    try:
        destination = copy_arm(args.plugin_root, args.arm, args.cases or list(DEFAULT_CASES))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(destination)
    print("Prepared only; no model calls were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
