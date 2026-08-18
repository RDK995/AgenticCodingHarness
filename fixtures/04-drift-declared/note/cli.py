"""C1 — CLI."""
import argparse
import json
import sys

import os
from pathlib import Path


def storage_path() -> Path:
    override = os.environ.get("NOTE_FILE")
    if override:
        return Path(override)
    base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(base) / "note" / "notes.jsonl"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="note")
    sub = parser.add_subparsers(dest="command", required=True)
    add_p = sub.add_parser("add")
    add_p.add_argument("text")
    sub.add_parser("list")
    args = parser.parse_args(argv)

    if args.command == "add":
        if not args.text.strip():
            print("note: refusing to store empty note", file=sys.stderr)
            return 1
        path = storage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(args.text) + "\n")
        return 0

    path = storage_path()
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            notes = [json.loads(line) for line in fh if line.strip()]
        for note in reversed(notes):
            print(note)
    return 0
