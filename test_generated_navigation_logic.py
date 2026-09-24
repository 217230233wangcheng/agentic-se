import itertools
import runpy
import unittest
from pathlib import Path


ARTIFACT = Path(__file__).parent / "artifacts" / "navigation_logic.py"
ACTIONS = {"FORWARD", "LEFT", "RIGHT", "STOP"}
SENSOR_KEYS = (
    "goal_ahead", "goal_on_left", "goal_on_right",
    "front_blocked", "left_blocked", "right_blocked",
)


def expected_action(state):
    goal_options = (
        ("goal_ahead", "front_blocked", "FORWARD"),
        ("goal_on_left", "left_blocked", "LEFT"),
        ("goal_on_right", "right_blocked", "RIGHT"),
    )
    for goal_key, blocked_key, action in goal_options:
        if state[goal_key] and not state[blocked_key]:
            return action
    for _, blocked_key, action in goal_options:
        if not state[blocked_key]:
            return action
    return "STOP"


class GeneratedNavigationLogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ARTIFACT.exists():
            raise FileNotFoundError(
                "Run test_developer.py first to create artifacts/navigation_logic.py."
            )
        cls.decide_next_move = staticmethod(
            runpy.run_path(str(ARTIFACT))["decide_next_move"]
        )

    def test_assignment_examples_and_edge_cases(self):
        base = dict.fromkeys(SENSOR_KEYS, False)
        cases = (
            ({"goal_ahead": True}, "FORWARD"),
            ({"goal_on_left": True}, "LEFT"),
            ({"goal_on_right": True}, "RIGHT"),
            ({"goal_on_left": True, "left_blocked": True}, "FORWARD"),
            ({"goal_on_right": True, "right_blocked": True,
              "front_blocked": True}, "LEFT"),
            ({"front_blocked": True}, "LEFT"),
            ({"front_blocked": True, "left_blocked": True}, "RIGHT"),
            ({"front_blocked": True, "left_blocked": True,
              "right_blocked": True}, "STOP"),
        )
        for changes, expected in cases:
            state = {**base, **changes}
            with self.subTest(state=state):
                self.assertEqual(self.decide_next_move(state), expected)

    def test_all_known_states(self):
        for values in itertools.product((False, True), repeat=len(SENSOR_KEYS)):
            state = dict(zip(SENSOR_KEYS, values))
            with self.subTest(state=state):
                actual = self.decide_next_move(state)
                self.assertIn(actual, ACTIONS)
                self.assertEqual(actual, expected_action(state))
        print("Checked all 64 combinations of the six supplied state flags.")


if __name__ == "__main__":
    unittest.main()
