# Architecture

## Status

AGREED

## Overview

Two components: a command-line front end that parses arguments and writes
output, and a store that appends notes to a single append-only file and reads
them back. Persistence is a JSON-Lines file rather than a database because the
requirements are single-user, single-machine, append-and-list only, and the
standard-library-only constraint rules out anything richer without cost.
Ordering is file order — the file is only ever appended to, so insertion order
is recoverable without storing timestamps.

## Components

### C1 — CLI

Responsibility: Parse `add` / `list` invocations, call the store, write output and exit codes.
Location: `note/cli.py`, with `note/__main__.py` as the `python -m note` entry point.
Depends on: C2
Realises: `note add <text>`, `note list` (newest first), empty-text rejection, exit codes.

### C2 — NoteStore

Responsibility: Append a note to the storage file and read all notes back in insertion order.
Location: `note/store.py`
Depends on: None
Realises: Notes survive restart; missing or unreadable storage file on first run.

## Interfaces

**C1 → C2** (in-process Python calls, the only boundary in the system):

```python
def add(text: str) -> None
    # Appends one note. Creates the storage file and parent directory if absent.

def read_all() -> list[str]
    # Returns every stored note in insertion order (oldest first).
    # Returns [] if the storage file does not exist.

def storage_path() -> pathlib.Path
    # Resolves NOTE_FILE if set, else the default path.
```

C1 owns presentation: it reverses `read_all()` to print newest first. C1 also
owns input validation — empty or whitespace-only text is rejected before `add`
is called, with an error on stderr and a non-zero exit, storing nothing
(agreed). C2 stores whatever string it is given and applies no ordering policy
beyond preserving insertion order.

## Data

A note is a single `str`. There is no note id, no timestamp, and no note object
— nothing in the requirements reads them.

Storage is one JSON-Lines file owned exclusively by C2: one JSON-encoded string
per line, e.g. `"buy milk"`. JSON encoding rather than raw text so that a note
containing a newline cannot corrupt the file or split into two notes.

Default path: `${XDG_DATA_HOME:-~/.local/share}/note/notes.jsonl`, overridable
by the `NOTE_FILE` environment variable (agreed). The override exists because the
acceptance criterion "a note added in one process run is listed in a later run"
cannot be tested without pointing two real process runs at a scratch file.

## Technology Choices

| Choice | Decision | Why | Rejected |
| --- | --- | --- | --- |
| Language | Python 3, stdlib only | Constraint | — |
| Argument parsing | `argparse` subparsers | Stdlib; gives `add`/`list` and usage errors free | Hand-rolled `sys.argv` parsing — more code, worse errors |
| Storage format | JSON Lines, append-only | Append is one `open(..., "a")` + `write`; newline-safe; no rewrite of existing data | Plain text lines (breaks on notes containing newlines); single JSON array (read-modify-write on every add); `sqlite3` (durable and stdlib, but a schema and connection lifecycle for an append-and-list workload nobody asked to query) |
| Ordering | File order, reversed for display | Append-only file makes insertion order authoritative | Stored timestamps — data no stated requirement reads |
| Storage location | XDG data dir, `NOTE_FILE` override | Standard location; override needed for cross-process testing | CWD-relative file — notes would silently differ per directory |

## Requirement Coverage

| Functional requirement | Component(s) |
| --- | --- |
| `note add <text>` stores a note | C1 (parse, validate), C2 (append) |
| `note list` prints all stored notes, newest first | C1 (reverse, print), C2 (read) |
| Notes survive restarting the tool | C2 |

## Risks

- **Concurrent writes.** Two simultaneous `note add` runs could interleave
  partial lines. Single-user single-machine is a confirmed requirement, and a
  single `write()` of a short line is atomic enough in practice, so there is no
  locking. Revisit if multi-process or sync ever becomes a goal.
- **Unreadable storage file.** If the file exists but contains a malformed line,
  C2 must fail loudly rather than silently dropping notes. This is a behaviour
  choice inside C2, not a structural one, but it is the one place data loss
  could hide.

## Open Architecture Questions

None

## Deviations
