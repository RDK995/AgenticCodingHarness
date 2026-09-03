"""A tiny notes store with a save hook."""


class NoteStore:
    def __init__(self):
        self._notes = []
        self._listeners = []

    def on_change(self, fn):
        self._listeners.append(fn)

    def add(self, text):
        if not text.strip():
            raise ValueError("note text must not be empty")
        self._notes.append(text)
        self._notify()

    def all(self):
        return list(self._notes)

    def _notify(self):
        for fn in self._listeners:
            try:
                fn(self.all())
            except Exception:
                # Swallow listener errors so one bad listener cannot break add().
                pass
