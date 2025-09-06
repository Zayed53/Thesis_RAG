import datetime
import subprocess
import re
import os
import json


project_path = r"F:\ResultsFromRunLLMs\MavenJavaProjectsFromGithub_deepseek_srcCode(Refined)\Contact-Management-System-main"
cmd = [
    r"C:\Program Files\Apache\Maven\apache-maven-3.9.10\bin\mvn.cmd",
    "-B", "-e",            # -B = batch mode, -e = print full stack traces
    "clean", "verify",     # full lifecycle build
    "-fae",                # fail at end (don’t stop on first error)
    "-Drat.skip=true",     # skip RAT plugin
    "-Dcheckstyle.skip=true",  # skip checkstyle
    "-Dsurefire.failIfNoSpecifiedTests=false",  # don’t fail if no tests
    "-Dmaven.test.failure.ignore=true"  # ignore test failures, continue
]

print(f"🔹 Running full build+verify in {project_path} ...")

process = subprocess.Popen(
    cmd,
    cwd=project_path,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

stdout, stderr = process.communicate()

print("\n##############stdout############\n")
print(stdout)
print("\n##############stdError############\n")
print(stderr)

report_dir = os.path.join(project_path, "target", "surefire-reports")

# ---------------------------
# 1. Collect test summaries
# ---------------------------
summary = {
    "total_tests": 0,
    "total_failures": 0,
    "total_errors": 0,
    "total_skipped": 0,
    "tests": []  # per-class details
}

# Each .txt file is one test class
for txt_file in os.listdir(report_dir):
    if txt_file.endswith(".txt"):
        filepath = os.path.join(report_dir, txt_file)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract test set name
        match_set = re.search(r"Test set: (.+)", content)
        test_class = match_set.group(1).strip() if match_set else txt_file

        # Extract tests run summary
        match_summary = re.search(
            r"Tests run:\s*(\d+), Failures:\s*(\d+), Errors:\s*(\d+), Skipped:\s*(\d+)", 
            content
        )
        if match_summary:
            run, failures, errors, skipped = map(int, match_summary.groups())
            summary["total_tests"] += run
            summary["total_failures"] += failures
            summary["total_errors"] += errors
            summary["total_skipped"] += skipped

            summary["tests"].append({
                "class": test_class,
                "tests_run": run,
                "failures": failures,
                "errors": errors,
                "skipped": skipped
            })

# ---------------------------
# 2. Save to JSON
# ---------------------------
output_json = os.path.join(project_path, "test_summary.json")
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=4)

print(f"✅ Test summary saved to {output_json}")