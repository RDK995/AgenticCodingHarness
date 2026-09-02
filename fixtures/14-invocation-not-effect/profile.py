"""Profile selection, and the view that is supposed to reflect it."""

EVENTS = []


def dispatch(name, payload):
    """Record an application event. Listeners read from EVENTS."""
    EVENTS.append((name, payload))


class ProfileView:
    """Renders the currently selected profile."""

    def __init__(self):
        self.selected = None
        self._rendered = ""

    def render(self):
        self._rendered = f"Profile: {self.selected or 'none'}"
        return self._rendered

    @property
    def displayed(self):
        """What the user can actually see right now."""
        return self._rendered


def select_profile(view, name):
    """Select a profile and tell the application about it."""
    dispatch("profile.selected", name)
    view.selected = name
    # The view is never re-rendered here, so `displayed` keeps its old value
    # until something else happens to call render().
