import ast
import json

from ollama import chat


MODEL = "qwen3:8b"

SYSTEM_PROMPT = """
You are the Developer Agent in a multi-agent robot navigation system.

You receive ONLY the validated plan created by the Planner Agent.
Your job is to convert that plan into valid Python navigation code.

Rules:
1. Return only Python code.
2. Do not include markdown code fences or explanations.
   Start the response with Python code, not a description of the solution.
3. Define a top-level function named decide_next_move(state). Other helper
   functions are allowed, but callers must only need decide_next_move(state).
4. state is a dictionary containing these six Boolean sensor values:
   goal_ahead, goal_on_left, goal_on_right,
   front_blocked, left_blocked, right_blocked.
5. If a goal direction is clear, move toward it. If more than one goal flag is
   true, check them in the order ahead, left, right.
6. If no indicated goal direction is clear, choose the first clear direction
   in this order: FORWARD, LEFT, RIGHT.
7. If all three directions are blocked, return STOP.
8. Use the supplied state for every decision. Do not use placeholder sensor
   functions or hard-coded sensor readings.
9. The robot may only return these actions:
   FORWARD, LEFT, RIGHT, STOP
10. The robot must not move into a blocked direction.
11. Follow the strategy, decisions, and stop condition in the supplied plan.
""".strip()


def clean_code(code):
    code = code.strip()

    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    elif code.startswith("```"):
        code = code[3:].strip()

    if code.endswith("```"):
        code = code[:-3].strip()

    return code


def validate_code(code):
    """
    Check that the model produced valid Python code with the required entry point.
    """
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Developer output must be non-empty Python code.")

    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        raise ValueError(f"Developer output is not valid Python: {error}")

    entry_points = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "decide_next_move"
    ]
    if len(entry_points) != 1:
        raise ValueError(
            "Developer output must define decide_next_move(state)."
        )
    arguments = entry_points[0].args
    if (len(arguments.posonlyargs) != 0 or len(arguments.args) != 1
            or arguments.args[0].arg != "state" or arguments.vararg is not None
            or arguments.kwonlyargs or arguments.kwarg is not None):
        raise ValueError("decide_next_move must accept exactly one state argument.")

    return code


def run_developer(plan):
    """
    Send the validated Planner artifact to Qwen,
    validate the generated Python code,
    and return the validated code.
    """
    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": (
                    "Create the Python navigation logic from this validated plan:\n\n"
                    + json.dumps(plan, indent=2)
                )
            }
        ],
        options={"temperature": 0},
        think=False,
    )

    code = response.message.content
    code = clean_code(code)

    return validate_code(code)
