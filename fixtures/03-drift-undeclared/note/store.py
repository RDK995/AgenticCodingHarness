"""C2 — NoteStore."""
import json
import os
from pathlib import Path


def storage_path() -> Path:
    override = os.environ.get("NOTE_FILE")
    if override:
        return Path(override)
    base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(base) / "note" / "notes.jsonl"


def add(text: str) -> None:
    path = storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(text) + "\n")


def read_all() -> list[str]:
    path = storage_path()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]
