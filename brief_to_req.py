from ollama import chat

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

    response = chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        options={
            "temperature": 0,
        },
    )

    requirements_text = response["message"]["content"].strip()
    print(requirements_text)


if __name__ == "__main__":
    main()
