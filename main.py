import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from analyst_agent import run_analyst
from benchmark_irsim import build_benchmark_report, run_world, WORLD_FILES
from developer_agent import run_developer, run_developer_revision
from planner_agent import run_planner
from reviewer_agent import run_reviewer
from reviewer_benchmark_agent import run_benchmark_reviewer
from runner import run_simulation
from test_agent import run_test_agent


PROJECT_DIR = Path(__file__).parent
ARTIFACTS_DIR = PROJECT_DIR / "artifacts"
GENERATED_DIR = PROJECT_DIR / "generated"
TRACE_FILE = PROJECT_DIR / "trace.log"


def log_event(agent_name, action):
    timestamp = datetime.now().isoformat(timespec="seconds")
    line = f"{timestamp} | {agent_name} | {action}"
    with TRACE_FILE.open("a", encoding="utf-8") as file:
        file.write(line + "\n")
    print(line)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")


def read_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_navigation_code(code, filename="navigation_logic.py"):
    targets = [
        PROJECT_DIR / filename,
        ARTIFACTS_DIR / filename,
        GENERATED_DIR / filename,
    ]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(code + "\n", encoding="utf-8")
    return targets


def run_generated_tests(test_file):
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file)],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    report = {
        "return_code": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    write_json(ARTIFACTS_DIR / "test_report.json", report)
    return report


def run_irsim_benchmark_pipeline():
    results = []
    for world_file in WORLD_FILES:
        if world_file.exists():
            results.append(run_world(world_file))
        else:
            results.append({
                "world_file": str(world_file.relative_to(PROJECT_DIR)),
                "reached_goal": False,
                "collision_or_done": True,
                "steps_taken": 0,
                "efficiency_status": "failed",
                "efficiency_passed": False,
                "error": "World file not found",
            })
    report = build_benchmark_report(results)
    write_json(ARTIFACTS_DIR / "irsim_benchmark_report.json", report)
    return report


def maybe_create_revision(review, benchmark_review, requirements, plan):
    needs_revision = (
        review.get("needs_revision", False)
        or benchmark_review.get("needs_revision", False)
    )
    if not needs_revision:
        return None

    original_code_path = ARTIFACTS_DIR / "navigation_logic.py"
    original_code = original_code_path.read_text(encoding="utf-8")
    revised_code = run_developer_revision(
        original_code=original_code,
        review_notes=review,
        benchmark_report=benchmark_review,
        requirements=requirements,
        plan=plan,
    )

    revised_path = ARTIFACTS_DIR / "navigation_logic_revised.py"
    revised_path.write_text(revised_code + "\n", encoding="utf-8")
    (GENERATED_DIR / "navigation_logic_revised.py").write_text(
        revised_code + "\n",
        encoding="utf-8"
    )
    return revised_path


def main():
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    GENERATED_DIR.mkdir(exist_ok=True)
    TRACE_FILE.write_text("", encoding="utf-8")

    brief_text = (PROJECT_DIR / "brief.txt").read_text(encoding="utf-8")
    log_event("Orchestrator", "Loaded brief.txt")

    requirements = run_analyst(brief_text)
    write_json(ARTIFACTS_DIR / "requirements.json", requirements)
    log_event("Analyst Agent", "Created artifacts/requirements.json")

    plan = run_planner(requirements)
    write_json(ARTIFACTS_DIR / "plan.json", plan)
    log_event("Planner Agent", "Created artifacts/plan.json")

    navigation_code = run_developer(plan)
    write_navigation_code(navigation_code)
    log_event("Developer Agent", "Created navigation_logic.py in project, artifacts, and generated folders")

    test_code = run_test_agent(requirements, plan)
    test_file = ARTIFACTS_DIR / "test_navigation_logic.py"
    test_file.write_text(test_code + "\n", encoding="utf-8")
    log_event("Test Agent", "Created artifacts/test_navigation_logic.py")

    test_report = run_generated_tests(test_file)
    log_event("Test Runner", f"Ran generated tests with return code {test_report['return_code']}")

    simulation_report = run_simulation()
    write_json(ARTIFACTS_DIR / "simulation_report.json", simulation_report)
    log_event("Simulation Runner", "Created artifacts/simulation_report.json")

    review = run_reviewer(simulation_report)
    write_json(ARTIFACTS_DIR / "review_report.json", review)
    log_event("Reviewer Agent", "Created artifacts/review_report.json")

    benchmark_report = run_irsim_benchmark_pipeline()
    log_event("IR-SIM Benchmark", "Created artifacts/irsim_benchmark_report.json")

    benchmark_review = run_benchmark_reviewer(benchmark_report)
    write_json(ARTIFACTS_DIR / "benchmark_review_report.json", benchmark_review)
    log_event("Benchmark Reviewer", "Created artifacts/benchmark_review_report.json")

    revised_path = maybe_create_revision(
        review,
        benchmark_review,
        requirements,
        plan,
    )
    if revised_path is None:
        log_event("Developer Revision Agent", "No revision required")
    else:
        log_event("Developer Revision Agent", f"Created {revised_path}")
        shutil.copyfile(revised_path, PROJECT_DIR / "navigation_logic.py")
        shutil.copyfile(revised_path, ARTIFACTS_DIR / "navigation_logic.py")
        shutil.copyfile(revised_path, GENERATED_DIR / "navigation_logic.py")
        retest_report = run_generated_tests(test_file)
        write_json(ARTIFACTS_DIR / "retest_report.json", retest_report)
        log_event("Test Runner", "Re-tested revised navigation logic")
        revised_simulation_report = run_simulation()
        write_json(
            ARTIFACTS_DIR / "simulation_report_revised.json",
            revised_simulation_report,
        )
        log_event("Simulation Runner", "Re-ran simulation for revised navigation logic")
        revised_benchmark_report = run_irsim_benchmark_pipeline()
        write_json(
            ARTIFACTS_DIR / "irsim_benchmark_report_revised.json",
            revised_benchmark_report,
        )
        log_event("IR-SIM Benchmark", "Re-ran benchmark for revised navigation logic")


if __name__ == "__main__":
    main()
