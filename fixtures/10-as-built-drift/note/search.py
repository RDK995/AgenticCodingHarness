"""Search support: reads the notes file and renders matching lines."""
import json

from note.store import storage_path


def _load() -> list[str]:
    path = storage_path()
    if not path.exists():
        return []
    notes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            notes.append(json.loads(line)["text"])
    return notes


def matching(term: str) -> list[str]:
    needle = term.lower()
    return [note for note in _load() if needle in note.lower()]
