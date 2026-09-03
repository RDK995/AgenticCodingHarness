import unittest

import profile as P


class SelectProfileTest(unittest.TestCase):
    def setUp(self):
        P.EVENTS.clear()

    def test_selecting_dispatches_the_event(self):
        view = P.ProfileView()
        P.select_profile(view, "fast")
        self.assertIn(("profile.selected", "fast"), P.EVENTS)

    def test_selecting_sets_the_selection(self):
        view = P.ProfileView()
        P.select_profile(view, "fast")
        self.assertEqual(view.selected, "fast")

    def test_view_shows_the_profile(self):
        view = P.ProfileView()
        P.select_profile(view, "fast")
        view.render()          # the test does the work the app should do
        self.assertEqual(view.displayed, "Profile: fast")


if __name__ == "__main__":
    unittest.main()
