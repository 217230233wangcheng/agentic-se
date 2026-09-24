import json
import unittest
from pathlib import Path

from analyst_agent import validate_requirements
from run_analyst import main


ARTIFACT = Path(__file__).parent / "artifacts" / "requirements.json"


class AnalystSmokeTest(unittest.TestCase):
    def test_real_brief_produces_requirements(self):
        main()
        requirements = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        validate_requirements(requirements)
        print(ARTIFACT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
