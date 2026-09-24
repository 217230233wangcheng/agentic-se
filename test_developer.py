import json
import unittest
from pathlib import Path

from developer_agent import validate_code
from planner_agent import validate_plan
from run_developer import main


PROJECT = Path(__file__).parent


class DeveloperSmokeTest(unittest.TestCase):
    def test_real_plan_produces_navigation_code(self):
        plan = json.loads(
            (PROJECT / "artifacts" / "plan.json").read_text(encoding="utf-8")
        )
        validate_plan(plan)
        main()
        artifact = PROJECT / "artifacts" / "navigation_logic.py"
        code = artifact.read_text(encoding="utf-8")
        validate_code(code)
        self.assertEqual(code, (PROJECT / "generated" / "navigation_logic.py").read_text(encoding="utf-8"))
        self.assertEqual(code, (PROJECT / "navigation_logic.py").read_text(encoding="utf-8"))
        print(code)


if __name__ == "__main__":
    unittest.main()
