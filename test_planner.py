import json
import unittest
from pathlib import Path

from analyst_agent import validate_requirements
from planner_agent import validate_plan
from run_planner import main


ARTIFACTS = Path(__file__).parent / "artifacts"


class PlannerSmokeTest(unittest.TestCase):
    def test_real_requirements_produce_plan(self):
        requirements = json.loads(
            (ARTIFACTS / "requirements.json").read_text(encoding="utf-8")
        )
        validate_requirements(requirements)
        main()
        plan_path = ARTIFACTS / "plan.json"
        validate_plan(json.loads(plan_path.read_text(encoding="utf-8")))
        print(plan_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
