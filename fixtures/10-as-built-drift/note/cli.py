"""C1 — CLI."""
from note import search, store


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: note add <text> | note list | note search <term>")
        return 1

    command, rest = argv[0], argv[1:]

    if command == "add":
        text = " ".join(rest).strip()
        if not text:
            return 1
        store.add(text)
        return 0

    if command == "list":
        for note in store.read_all():
            print(note)
        return 0

    if command == "search":
        term = " ".join(rest).strip()
        if not term:
            return 1
        for note in search.matching(term):
            print(note)
        return 0

    return 1
