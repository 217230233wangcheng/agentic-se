from pathlib import Path
import json

from planner_agent import run_planner


REQUIREMENTS_FILE = Path("artifacts") / "requirements.json"
PLAN_FILE = Path("artifacts") / "plan.json"


def main():
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(
            "artifacts/requirements.json was not found. Run run_analyst.py first."
        )

    with REQUIREMENTS_FILE.open("r", encoding="utf-8") as file:
        requirements = json.load(file)

    plan = run_planner(requirements)

    PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)

    with PLAN_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            plan,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"Validated plan saved to {PLAN_FILE}")


if __name__ == "__main__":
    main()
