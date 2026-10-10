import json
from json import JSONDecodeError

from ollama import chat


MODEL = "qwen3:8b"
REQUIRED_KEYS = {
    "issue",
    "likely_cause",
    "recommendation",
    "safety_passed",
    "goal_completion_passed",
    "efficiency_passed",
    "needs_revision",
}

SYSTEM_PROMPT = """
You are the Benchmark Reviewer Agent in a multi-agent robot navigation system.

Review the IR-SIM benchmark report and return only valid JSON using exactly
these keys:
issue, likely_cause, recommendation, safety_passed, goal_completion_passed,
efficiency_passed, needs_revision.

Rules:
1. Do not include markdown code fences or explanations.
2. safety_passed, goal_completion_passed, efficiency_passed, and
   needs_revision must be booleans.
3. Base pass/fail booleans on the measured benchmark report.
4. Recommend code revision if safety, goal completion, or efficiency fails.
""".strip()


def clean_json_text(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def validate_benchmark_review(review):
    if not isinstance(review, dict):
        raise ValueError("Benchmark review must be a dictionary.")
    if set(review.keys()) != REQUIRED_KEYS:
        raise ValueError("Benchmark review has invalid keys.")
    for key in ("issue", "likely_cause", "recommendation"):
        if not isinstance(review[key], str):
            raise ValueError(f"{key} must be a string.")
    for key in (
            "safety_passed",
            "goal_completion_passed",
            "efficiency_passed",
            "needs_revision"):
        if not isinstance(review[key], bool):
            raise ValueError(f"{key} must be a boolean.")
    return review


def build_deterministic_review(benchmark_report):
    results = benchmark_report.get("results", [])
    unsafe = any(
        item.get("collision_or_done") and not item.get("reached_goal")
        for item in results
    )
    safety_passed = not unsafe
    goal_completion_passed = benchmark_report.get("success_rate", 0) >= 1.0
    efficiency_passed = (
        benchmark_report.get("inefficient_success_worlds", 0) == 0
        and benchmark_report.get("efficiency_rate", 0) >= 1.0
    )
    needs_revision = not (
        safety_passed and goal_completion_passed and efficiency_passed
    )

    if not safety_passed:
        issue = "Unsafe benchmark behavior detected"
        likely_cause = "At least one world ended without reaching the goal."
        recommendation = "Revise the navigation logic to avoid unsafe terminal states and improve obstacle handling."
    elif not goal_completion_passed:
        issue = "Goal completion failure"
        likely_cause = "The robot failed to reach the goal in every benchmark world."
        recommendation = "Revise the navigation logic to make stronger progress toward the goal while preserving safety."
    elif not efficiency_passed:
        issue = "Successful but inefficient navigation"
        likely_cause = "At least one successful run exceeded the efficient step limit."
        recommendation = "Revise the navigation logic to reduce unnecessary turns and improve path efficiency."
    else:
        issue = "No benchmark issue detected"
        likely_cause = "All worlds passed safety, goal completion, and efficiency checks."
        recommendation = "No revision is required based on the benchmark report."

    return {
        "issue": issue,
        "likely_cause": likely_cause,
        "recommendation": recommendation,
        "safety_passed": safety_passed,
        "goal_completion_passed": goal_completion_passed,
        "efficiency_passed": efficiency_passed,
        "needs_revision": needs_revision,
    }


def run_benchmark_reviewer(benchmark_report):
    deterministic = build_deterministic_review(benchmark_report)
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
                        "benchmark_report": benchmark_report,
                        "deterministic_review": deterministic,
                    },
                    indent=2
                )
            }
        ],
        format="json",
        options={"temperature": 0},
        think=False,
    )

    try:
        review = json.loads(clean_json_text(response.message.content))
        review = validate_benchmark_review(review)
    except (JSONDecodeError, ValueError):
        review = deterministic

    for key in (
            "safety_passed",
            "goal_completion_passed",
            "efficiency_passed",
            "needs_revision"):
        review[key] = deterministic[key]
    return validate_benchmark_review(review)
