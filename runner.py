import importlib.util
import json
from pathlib import Path


PROJECT_DIR = Path(__file__).parent
NAVIGATION_LOGIC_FILE = PROJECT_DIR / "artifacts" / "navigation_logic.py"
REPORT_FILE = PROJECT_DIR / "artifacts" / "simulation_report.json"
ACTIONS = {"FORWARD", "LEFT", "RIGHT", "STOP"}
SENSOR_KEYS = (
    "goal_ahead", "goal_on_left", "goal_on_right",
    "front_blocked", "left_blocked", "right_blocked",
)


def load_decide_next_move(path=NAVIGATION_LOGIC_FILE):
    if not path.exists():
        raise FileNotFoundError(f"Navigation logic file not found: {path}")

    spec = importlib.util.spec_from_file_location("navigation_logic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "decide_next_move"):
        raise ValueError("navigation_logic.py must define decide_next_move(state).")
    return module.decide_next_move


def expected_action(state):
    goal_options = (
        ("goal_ahead", "front_blocked", "FORWARD"),
        ("goal_on_left", "left_blocked", "LEFT"),
        ("goal_on_right", "right_blocked", "RIGHT"),
    )
    for goal_key, blocked_key, action in goal_options:
        if state[goal_key] and not state[blocked_key]:
            return action
    for _, blocked_key, action in goal_options:
        if not state[blocked_key]:
            return action
    return "STOP"


def scenario(name, changes):
    state = dict.fromkeys(SENSOR_KEYS, False)
    state.update(changes)
    return {
        "name": name,
        "state": state,
        "expected": expected_action(state),
    }


def build_scenarios():
    return [
        scenario("goal ahead clear", {"goal_ahead": True}),
        scenario("goal left clear", {"goal_on_left": True}),
        scenario("goal right clear", {"goal_on_right": True}),
        scenario("left goal blocked fallback forward", {
            "goal_on_left": True,
            "left_blocked": True,
        }),
        scenario("right goal blocked fallback left", {
            "goal_on_right": True,
            "right_blocked": True,
            "front_blocked": True,
        }),
        scenario("front blocked fallback left", {"front_blocked": True}),
        scenario("front and left blocked fallback right", {
            "front_blocked": True,
            "left_blocked": True,
        }),
        scenario("all directions blocked stop", {
            "front_blocked": True,
            "left_blocked": True,
            "right_blocked": True,
        }),
        scenario("multiple goals use ahead first", {
            "goal_ahead": True,
            "goal_on_left": True,
            "goal_on_right": True,
        }),
        scenario("ahead blocked then left goal", {
            "goal_ahead": True,
            "goal_on_left": True,
            "front_blocked": True,
        }),
    ]


def run_simulation():
    decide_next_move = load_decide_next_move()
    results = []

    for item in build_scenarios():
        actual = decide_next_move(dict(item["state"]))
        passed = actual == item["expected"] and actual in ACTIONS
        results.append({
            "name": item["name"],
            "state": item["state"],
            "expected": item["expected"],
            "actual": actual,
            "passed": passed,
        })

    total = len(results)
    passed_count = sum(1 for item in results if item["passed"])
    failed_count = total - passed_count
    report = {
        "total_scenarios": total,
        "passed": passed_count,
        "failed": failed_count,
        "success_rate": passed_count / total if total else 0,
        "results": results,
    }
    return report


def main():
    report = run_simulation()
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
