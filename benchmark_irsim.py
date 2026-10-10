import ast
import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).parent
ARTIFACTS_DIR = PROJECT_DIR / "artifacts"
IRSIM_REPORT_FILE = ARTIFACTS_DIR / "irsim_report.json"
BENCHMARK_REPORT_FILE = ARTIFACTS_DIR / "irsim_benchmark_report.json"
WORLD_FILES = [
    PROJECT_DIR / "irsim_worlds" / "world_easy.yaml",
    PROJECT_DIR / "irsim_worlds" / "world_medium.yaml",
    PROJECT_DIR / "irsim_worlds" / "world_difficult.yaml",
    PROJECT_DIR / "irsim_worlds" / "world_custom.yaml",
]


def load_report_from_stdout(output):
    for line in reversed(output.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return ast.literal_eval(line)
            except (SyntaxError, ValueError):
                continue
    return None


def run_world(world_file):
    command = [
        sys.executable,
        str(PROJECT_DIR / "test_irsim_with_agent.py"),
        str(world_file),
    ]
    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")
    completed = subprocess.run(
        command,
        cwd=PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    report = None
    if IRSIM_REPORT_FILE.exists():
        with IRSIM_REPORT_FILE.open("r", encoding="utf-8") as file:
            report = json.load(file)
    if report is None:
        report = load_report_from_stdout(completed.stdout)
    if report is None:
        report = {
            "reached_goal": False,
            "collision_or_done": True,
            "steps_taken": 0,
            "efficiency_status": "failed",
            "efficiency_passed": False,
        }

    report.update({
        "world_file": str(world_file.relative_to(PROJECT_DIR)),
        "return_code": completed.returncode,
        "stdout_tail": completed.stdout[-1000:],
        "stderr_tail": completed.stderr[-1000:],
    })
    return report


def build_benchmark_report(results):
    total = len(results)
    reached_goal_count = sum(1 for item in results if item.get("reached_goal"))
    efficient_count = sum(1 for item in results if item.get("efficiency_status") == "efficient")
    inefficient_success_count = sum(
        1 for item in results
        if item.get("efficiency_status") == "acceptable_but_inefficient"
    )
    failed_count = total - reached_goal_count
    total_steps = sum(int(item.get("steps_taken", 0) or 0) for item in results)

    return {
        "total_worlds": total,
        "goals_reached": reached_goal_count,
        "success_rate": reached_goal_count / total if total else 0,
        "efficient_worlds": efficient_count,
        "inefficient_success_worlds": inefficient_success_count,
        "failed_worlds": failed_count,
        "efficiency_rate": efficient_count / total if total else 0,
        "average_steps_taken": total_steps / total if total else 0,
        "results": results,
    }


def main():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    results = [run_world(world_file) for world_file in WORLD_FILES]
    report = build_benchmark_report(results)

    with BENCHMARK_REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
