import itertools

from artifacts.navigation_logic import decide_next_move


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


def test_goal_direction_priority():
    base = dict.fromkeys(SENSOR_KEYS, False)
    assert decide_next_move({**base, "goal_ahead": True}) == "FORWARD"
    assert decide_next_move({**base, "goal_on_left": True}) == "LEFT"
    assert decide_next_move({**base, "goal_on_right": True}) == "RIGHT"


def test_fallback_and_stop_behavior():
    base = dict.fromkeys(SENSOR_KEYS, False)
    assert decide_next_move({**base, "goal_on_left": True, "left_blocked": True}) == "FORWARD"
    assert decide_next_move({**base, "front_blocked": True}) == "LEFT"
    assert decide_next_move({**base, "front_blocked": True, "left_blocked": True}) == "RIGHT"
    assert decide_next_move({**base, "front_blocked": True, "left_blocked": True, "right_blocked": True}) == "STOP"


def test_all_possible_states():
    for values in itertools.product((False, True), repeat=len(SENSOR_KEYS)):
        state = dict(zip(SENSOR_KEYS, values))
        actual = decide_next_move(state)
        assert actual in ACTIONS
        assert actual == expected_action(state)

