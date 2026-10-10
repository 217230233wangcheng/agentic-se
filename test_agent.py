import ast
import json

from ollama import chat


MODEL = "qwen3:8b"

SYSTEM_PROMPT = """
You are the Test Agent in a multi-agent robot navigation system.

Your job is to generate pytest-style tests for the generated
decide_next_move(state) function.

Inputs:
- validated requirements from the Analyst Agent
- validated plan from the Planner Agent

The generated tests must:
1. Import decide_next_move from artifacts.navigation_logic.
2. Test goal-ahead, goal-left, and goal-right behavior.
3. Test fallback behavior when the goal direction is blocked.
4. Test that STOP is returned when all directions are blocked.
5. Test all 64 combinations of the six Boolean state flags.
6. Assert that only FORWARD, LEFT, RIGHT, or STOP is returned.
7. Return only Python test code.
8. Do not include markdown code fences or explanations.
""".strip()


REQUIRED_KEYWORDS = (
    "decide_next_move",
    "assert",
    "goal_ahead",
    "goal_on_left",
    "goal_on_right",
    "front_blocked",
    "left_blocked",
    "right_blocked",
    "STOP",
)


def clean_code(code):
    code = code.strip()
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    elif code.startswith("```"):
        code = code[3:].strip()
    if code.endswith("```"):
        code = code[:-3].strip()
    return code


def validate_test_code(code):
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Test Agent output must be non-empty Python code.")
    if "```" in code:
        raise ValueError("Test Agent output must not contain markdown fences.")

    try:
        ast.parse(code)
    except SyntaxError as error:
        raise ValueError(f"Test Agent output is not valid Python: {error}")

    missing = [keyword for keyword in REQUIRED_KEYWORDS if keyword not in code]
    if missing:
        raise ValueError(f"Test Agent output is missing required keywords: {missing}")

    return code


def build_fallback_tests():
    return '''import itertools

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
'''


def run_test_agent(requirements, plan):
    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "requirements": requirements,
                        "plan": plan,
                    },
                    indent=2
                )
            }
        ],
        options={"temperature": 0},
        think=False,
    )

    code = clean_code(response.message.content)
    try:
        return validate_test_code(code)
    except ValueError:
        return validate_test_code(build_fallback_tests())
