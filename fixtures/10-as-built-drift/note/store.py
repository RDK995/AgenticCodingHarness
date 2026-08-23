"""C2 — NoteStore. Owns the notes file."""
import json
import os
import pathlib


def storage_path() -> pathlib.Path:
    root = os.environ.get("NOTE_HOME", str(pathlib.Path.home() / ".note"))
    return pathlib.Path(root) / "notes.jsonl"


def add(text: str) -> None:
    path = storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"text": text}) + "\n")


def read_all() -> list[str]:
    path = storage_path()
    if not path.exists():
        return []
    notes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            notes.append(json.loads(line)["text"])
    return notes
