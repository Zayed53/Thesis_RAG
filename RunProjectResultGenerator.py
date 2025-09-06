import datetime
import subprocess
import re
import os
import json
import javalang
import glob
import xml.etree.ElementTree as ET

# ---------------------------
# 1. Run Maven compile
# ---------------------------
def run_maven_command(project_path, goal, log_prefix="compile", log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{log_prefix}_log_{timestamp}.txt")

    cmd = [
        r"C:\Program Files\Apache\Maven\apache-maven-3.9.10\bin\mvn.cmd",
        "-B", "-e",
        "clean", "test-compile",  # separate strings
        "-Drat.skip=true",
        "-Dcheckstyle.skip=true",
        "-Dsurefire.failIfNoSpecifiedTests=false"
    ]


    print(f"🔹 Running {goal} in {project_path} ...")
    process = subprocess.Popen(
        cmd,
        cwd=project_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate()

    with open(log_file, "w", encoding="utf-8") as f:
        f.write("==== STDOUT ====\n")
        f.write(stdout)
        f.write("\n==== STDERR ====\n")
        f.write(stderr or "")

    print(f"📄 Full log saved to {log_file}")

    return stdout.splitlines(), stderr

# ---------------------------
# 2. Parse compile errors
# ---------------------------
def parse_errors(output_lines):
    errors = []
    error_counts = {
        "missing_package": 0,
        "cannot_find_symbol": 0,
        "syntax_error": 0,
        "other": 0
    }

    pattern = re.compile(r"\[ERROR\]\s(.+\.java):\[(\d+),(\d+)\]\s(.+)")

    for line in output_lines:
        match = pattern.search(line)
        if match:
            filepath, row, col, message = match.groups()
            filepath = filepath.strip()

            # categorize
            if "package" in message and "does not exist" in message:
                category = "missing_package"
            elif "cannot find symbol" in message:
                category = "cannot_find_symbol"
            elif "not a statement" in message or "expected" in message:
                category = "syntax_error"
            else:
                category = "other"

            error_counts[category] += 1
            errors.append({
                "file": filepath,
                "line": int(row),
                "col": int(col),
                "message": message,
                "category": category
            })

    return errors, error_counts

# ---------------------------
# 3. Syntactic correctness (javalang)
# ---------------------------
def check_syntax_in_tests(test_dir):
    syntax_results = []
    syntactic_correctness_count=0
    for root, _, files in os.walk(test_dir):
        for f in files:
            if f.endswith(".java"):
                filepath = os.path.join(root, f)
                with open(filepath, "r", encoding="utf-8") as src:
                    code = src.read()
                try:
                    javalang.parse.parse(code)
                    syntax_results.append({"file": filepath, "syntax_ok": True})
                except javalang.parser.JavaSyntaxError as e:
                    syntax_results.append({
                        "file": filepath,
                        "syntax_ok": False,
                        "error": str(e)
                    })
                    syntactic_correctness_count+=1
    return syntax_results , syntactic_correctness_count


# ---------------------------
# parse surefire_reports for test
# ---------------------------
def parse_surefire_reports(report_dir):
    results = []
    summary = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}

    for xml_file in glob.glob(os.path.join(report_dir, "TEST-*.xml")):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for case in root.findall("testcase"):
            test_name = case.get("name")
            classname = case.get("classname")
            status = "passed"
            error_msg = None
            error_type = None

            failure = case.find("failure")
            error = case.find("error")
            skipped = case.find("skipped")

            if failure is not None:
                status = "failed"
                error_msg = failure.get("message")
                error_type = failure.get("type")
                summary["failed"] += 1
            elif error is not None:
                status = "error"
                error_msg = error.get("message")
                error_type = error.get("type")
                summary["errors"] += 1
            elif skipped is not None:
                status = "skipped"
                summary["skipped"] += 1
            else:
                summary["passed"] += 1

            results.append({
                "class": classname,
                "test": test_name,
                "status": status,
                "error_type": error_type,
                "error_message": error_msg
            })

    return summary, results
# ---------------------------
# 4. Execution correctness (mvn test)
# ---------------------------
def run_tests(project_path):
    output, _ = run_maven_command(project_path, "test", log_prefix="test")
    results = {
        "passed": 0,
        "failed": 0,
        "errors": 0
    }

    # Parse Surefire summary lines
    for line in output:
        if "Tests run:" in line and "Failures:" in line and "Errors:" in line:
            # Example: "Tests run: 5, Failures: 1, Errors: 0, Skipped: 0"
            match = re.search(r"Tests run:\s*(\d+), Failures:\s*(\d+), Errors:\s*(\d+)", line)
            if match:
                total, failures, errors = map(int, match.groups())
                results["passed"] += total - failures - errors
                results["failed"] += failures
                results["errors"] += errors
    return results

def run_tests(project_path):
    # Run mvn test
    run_maven_command(project_path, "test", log_prefix="test")
    
    # Parse Surefire reports
    report_dir = os.path.join(project_path, "target", "surefire-reports")
    summary, details = parse_surefire_reports(report_dir)
    
    return {
        "summary": summary,
        "details": details
    }

# ---------------------------
# 5. Main pipeline
# ---------------------------
def process_project(project_path, report_file="evaluation_report.json"):
    # Step 1: Syntax correctness
    syntax_results, syntactic_correctness_count = check_syntax_in_tests(os.path.join(project_path, "src", "test", "java"))

    # Step 2: Compilation correctness
    compile_output, _ = run_maven_command(project_path, "clean test-compile", log_prefix=f"compile_{os.path.basename(project_path)}")
    errors, error_counts = parse_errors(compile_output)

    # Step 3: Execution correctness
    # execution_results = run_tests(project_path)
    error_counts["syntactic_correctness_count"] = syntactic_correctness_count
    # Build JSON report
    report = {
        "project": project_path,
        "syntactic_correctness": syntax_results,
        "compilation_correctness": {
            "error_count":len(errors),
            "errors": errors,
            "error_counts": error_counts
        },
        # "execution_correctness": execution_results
    }

    # Step 3: Append to file instead of overwrite
    if os.path.exists(report_file):
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = [data]  # ensure it's a list
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    data.append(report)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"\n✅ [Report Saved] {report_file}")




# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    project_path = r"F:\ResultsFromRunLLMs\MavenJavaProjectsFromGithub_deepseek_srcCode(Refined)\Contact-Management-System-main"
    process_project(project_path, "evaluation_report.json")
