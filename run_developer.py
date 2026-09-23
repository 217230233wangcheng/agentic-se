## the logic is similar to the run_planner and run_analyst files
from pathlib import Path
import json

from developer_agent import run_developer


PLAN_FILE = Path("artifacts") / "plan.json"
OUTPUT_FILE = Path("navigation_logic.py")


def main():
    if not PLAN_FILE.exists():
        raise FileNotFoundError(
            "artifacts/plan.json was not found. Run run_planner.py first."
        )

    with PLAN_FILE.open("r", encoding="utf-8") as file:
        plan = json.load(file)

    code = run_developer(plan)

    OUTPUT_FILE.write_text(code, encoding="utf-8")

    print(f"Generated code saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()