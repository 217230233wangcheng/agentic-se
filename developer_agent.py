from ollama import chat
import ast


MODEL = "qwen3:8b"

SYSTEM_PROMPT = """
You are the Developer Agent in a multi-agent robot navigation system.

You receive ONLY the validated plan created by the Planner Agent.
Your job is to convert that plan into valid Python navigation code.

Rules:
1. Return only Python code.
2. Do not include markdown code fences or explanations.
3. The code must contain at least one function for robot navigation.
4. The robot may only return these actions:
   FORWARD, LEFT, RIGHT, STOP
5. The robot must not move into a blocked direction.
6. If all possible directions are blocked, the robot must return STOP.
7. Follow the strategy, decisions, and stop condition in the supplied plan.
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
    Check that the model produced valid Python code
    and that the code contains at least one function.
    """
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Developer output must be non-empty Python code.")

    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        raise ValueError(f"Developer output is not valid Python: {error}")

    has_function = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for node in ast.walk(tree)
    )

    if not has_function:
        raise ValueError(
            "Developer output must contain at least one navigation function."
        )

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
                    + str(plan)
                )
            }
        ]
    )

    code = response.message.content
    code = clean_code(code)

    return validate_code(code)
