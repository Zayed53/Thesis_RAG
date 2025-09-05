import datetime
import subprocess
import re
import os
import json
import javalang

# ---------------------------
# 1. Run Maven compile
# ---------------------------
def run_maven_compile(project_path, log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"compile_log_{timestamp}.txt")

    cmd = [
        r"C:\Program Files\Apache\Maven\apache-maven-3.9.10\bin\mvn.cmd",
        "-B", "-e", "clean", "test-compile",
        "-Drat.skip=true",
        "-Dcheckstyle.skip=true",
        "-Dsurefire.failIfNoSpecifiedTests=false"
    ]

    print(f"🔹 Running compile in {project_path} ...")
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

    return stdout.splitlines()  # return output lines for parsing

# ---------------------------
# 2. Parse errors per file
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

    ErrorCount=0
    for line in output_lines:
        match = pattern.search(line)
        if match:
            filepath, row, col, message = match.groups()
            filepath = filepath.strip()
            ErrorCount+=1
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
    print(ErrorCount)
    return errors, error_counts

# ---------------------------
# 3. Delete files causing errors
# ---------------------------
# def delete_error_files(errors):
#     deleted_files = set()
#     for e in errors:
#         filepath = e["file"]
#         if os.path.exists(filepath):
#             try:
#                 os.remove(filepath)
#                 print(f"[Deleted] {filepath} due to compile errors")
#                 deleted_files.add(filepath)
#             except Exception as ex:
#                 print(f"[Failed to delete] {filepath}: {ex}")
#     return deleted_files

# ---------------------------
# 4. Main pipeline
# ---------------------------
def process_project(project_path, report_file="compile_report.json"):
    output = run_maven_compile(project_path)
    errors, error_counts = parse_errors(output)

    # Delete files causing errors
    # deleted_files = delete_error_files(errors)

    # Save JSON report
    report = {
        "project": project_path,
        "errors": errors,
        "error_counts": error_counts,
        # "deleted_files": list(deleted_files)
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print(f"\n[Report Saved] {report_file}")

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    project_path = r"F:\Thesis_SELAB_PMT\java_project - Copy\apollo"
    process_project(project_path)
