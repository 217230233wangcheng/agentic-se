import json
from pathlib import Path

from analyst_agent import run_analyst


def main():
    project_dir = Path(__file__).parent
    brief_path = project_dir / "brief.txt"
    artifacts_dir = project_dir / "artifacts"
    output_path = artifacts_dir / "requirements.json"

    brief_text = brief_path.read_text(encoding="utf-8")
    requirements = run_analyst(brief_text)

    artifacts_dir.mkdir(exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(requirements, file, indent=2)
        file.write("\n")

    print(f"Saved validated requirements to {output_path}")


if __name__ == "__main__":
    main()
