import json
from json import JSONDecodeError

from ollama import chat


MODEL = "qwen3:8b"
REQUIRED_KEYS = {"issue", "likely_cause", "recommendation", "needs_revision"}

SYSTEM_PROMPT = """
You are the Reviewer Agent in a multi-agent robot navigation system.

Review the simulation report and return only valid JSON using exactly this
schema:

{
  "issue": "string",
  "likely_cause": "string",
  "recommendation": "string",
  "needs_revision": true
}

Rules:
1. Do not include markdown code fences or explanations.
2. needs_revision must be a boolean.
3. If every simulation scenario passed, needs_revision should be false.
4. If any simulation scenario failed, identify the problem and recommend a fix.
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


def validate_review(review):
    if not isinstance(review, dict):
        raise ValueError("Reviewer output must be a dictionary.")
    if set(review.keys()) != REQUIRED_KEYS:
        raise ValueError("Reviewer output has invalid keys.")
    for key in ("issue", "likely_cause", "recommendation"):
        if not isinstance(review[key], str):
            raise ValueError(f"{key} must be a string.")
    if not isinstance(review["needs_revision"], bool):
        raise ValueError("needs_revision must be a boolean.")
    return review


def deterministic_review(simulation_report):
    failed = simulation_report.get("failed", 0)
    if failed:
        return {
            "issue": "Simulation failures detected",
            "likely_cause": "The generated navigation logic did not match one or more expected decisions.",
            "recommendation": "Revise decide_next_move so it prioritizes clear goal directions, avoids blocked directions, and stops when all directions are blocked.",
            "needs_revision": True,
        }
    return {
        "issue": "No simulation issue detected",
        "likely_cause": "All deterministic simulation scenarios passed.",
        "recommendation": "No revision is required based on the simple simulation report.",
        "needs_revision": False,
    }


def run_reviewer(simulation_report):
    baseline = deterministic_review(simulation_report)
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
                        "simulation_report": simulation_report,
                        "deterministic_review": baseline,
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
        review = validate_review(review)
    except (JSONDecodeError, ValueError):
        review = baseline

    review["needs_revision"] = baseline["needs_revision"]
    if baseline["needs_revision"]:
        review["issue"] = review["issue"] or baseline["issue"]
    return validate_review(review)
