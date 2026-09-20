import json
from json import JSONDecodeError
from urllib.error import URLError
from urllib.request import Request, urlopen


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"
EXPECTED_KEYS = {"goal", "allowed_actions", "safe_stop", "avoid_obstacles"}
EXPECTED_ACTIONS = ["FORWARD", "LEFT", "RIGHT", "STOP"]


def build_prompt(brief_text):
    return f"""
You are an Analyst Agent acting as a software requirements engineer.

Your task is to read a human-written robot navigation brief and convert it
into explicit software requirements.

Rules:
- Return only one valid JSON object.
- Do not include Markdown, explanations, comments, or extra text.
- Do not include thinking steps.
- The JSON object must contain exactly these keys:
  "goal", "allowed_actions", "safe_stop", "avoid_obstacles"
- "goal" must be a string describing the navigation objective.
- "allowed_actions" must be exactly ["FORWARD", "LEFT", "RIGHT", "STOP"].
- "safe_stop" must be true if the robot must stop when no safe move exists.
- "avoid_obstacles" must be true if the robot must never move into a blocked direction.

Required output structure:
{{
  "goal": "string",
  "allowed_actions": ["FORWARD", "LEFT", "RIGHT", "STOP"],
  "safe_stop": true,
  "avoid_obstacles": true
}}

Brief text:
\"\"\"
{brief_text}
\"\"\"
""".strip()


def call_qwen(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0
        },
    }
    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, JSONDecodeError) as exc:
        raise RuntimeError(
            "Could not call Ollama. Make sure Ollama is running and qwen3:8b is installed."
        ) from exc

    return data.get("response", "")


def extract_json_text(model_response):
    cleaned = model_response.strip()
    decoder = json.JSONDecoder()

    for index, character in enumerate(cleaned):
        if character == "{":
            try:
                _, end_index = decoder.raw_decode(cleaned[index:])
            except JSONDecodeError:
                continue
            return cleaned[index:index + end_index]

    raise ValueError("Qwen did not return a valid JSON object.")


def validate_requirements(result):
    if not isinstance(result, dict):
        raise ValueError("Requirements must be a dictionary.")

    actual_keys = set(result.keys())
    if actual_keys != EXPECTED_KEYS:
        missing = EXPECTED_KEYS - actual_keys
        extra = actual_keys - EXPECTED_KEYS
        raise ValueError(f"Invalid requirement keys. Missing: {missing}. Extra: {extra}.")

    if not isinstance(result["goal"], str) or not result["goal"].strip():
        raise ValueError("The goal must be a non-empty string.")

    if not isinstance(result["allowed_actions"], list):
        raise ValueError("allowed_actions must be a list.")

    if result["allowed_actions"] != EXPECTED_ACTIONS:
        raise ValueError(
            f"allowed_actions must be exactly {EXPECTED_ACTIONS}."
        )

    if not isinstance(result["safe_stop"], bool):
        raise ValueError("safe_stop must be a boolean.")

    if not isinstance(result["avoid_obstacles"], bool):
        raise ValueError("avoid_obstacles must be a boolean.")

    return result


def run_analyst(brief_text):
    prompt = build_prompt(brief_text)
    model_response = call_qwen(prompt)
    json_text = extract_json_text(model_response)
    requirements = json.loads(json_text)
    return validate_requirements(requirements)
