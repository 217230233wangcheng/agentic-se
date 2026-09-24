## the logic is similar to the run_planner and run_analyst files
from pathlib import Path
import json

from developer_agent import run_developer


PLAN_FILE = Path("artifacts") / "plan.json"
OUTPUT_FILES = (
    Path("navigation_logic.py"),
    Path("artifacts") / "navigation_logic.py",
    Path("generated") / "navigation_logic.py",
)


def main():
    if not PLAN_FILE.exists():
        raise FileNotFoundError(
            "artifacts/plan.json was not found. Run run_planner.py first."
        )

    with PLAN_FILE.open("r", encoding="utf-8") as file:
        plan = json.load(file)

    code = run_developer(plan)

    for output_file in OUTPUT_FILES:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code + "\n", encoding="utf-8")

    for output_file in OUTPUT_FILES:
        print(f"Generated code saved to {output_file}")


if __name__ == "__main__":
    main()
