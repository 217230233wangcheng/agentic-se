import json
from urllib.request import Request, urlopen

# Ollama API endpoint and model name
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"

# Main function give brief text and return requirements text
def main():
    with open("brief.txt", "r", encoding="utf-8") as file:
        brief_text = file.read()

    prompt = f"""
You are a software requirements engineer.

Read the following robot navigation brief and convert it into clear software
requirements. Focus on the robot's goal, allowed actions, obstacle avoidance,
safe stopping behavior, and testing expectations.

Brief:
\"\"\"
{brief_text}
\"\"\"
""".strip()

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
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

    with urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))

    requirements_text = data["response"].strip()
    print(requirements_text)


if __name__ == "__main__":
    main()
