import subprocess
import datetime
import os

def compile_maven_project(project_path, log_dir="logs"):
    """
    Runs `mvn clean test-compile` on the given project path,
    saves logs, and extracts compile errors for all test classes.
    """

    # Make log directory
    os.makedirs(log_dir, exist_ok=True)

    # Timestamped log file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"compile_log_{timestamp}.txt")

    # Maven command (quote -D props if using PowerShell)
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

    # Save full log
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("==== STDOUT ====\n")
        f.write(stdout)
        f.write("\n==== STDERR ====\n")
        f.write(stderr)

    print(f"📄 Full log saved to {log_file}")

    # Extract compile errors
    errors = []
    for line in stdout.splitlines() + stderr.splitlines():
        if "[ERROR]" in line:
            errors.append(line.strip())

    # Prepare result
    if process.returncode == 0:
        print("✅ Compile successful!")
        return {"status": "success", "errors": []}
    else:
        print(f"❌ Compile failed with {len(errors)} error messages")
        return {"status": "failed", "errors": errors}


# Example usage
if __name__ == "__main__":
    project_path = r"F:\Thesis_SELAB_PMT\PROJECTS_ALL - Maven - CodeLLama_srccode\The Algorithms"
    result = compile_maven_project(project_path)

    print("\n=== Compile Result ===")
    for err in result["errors"]:
        print(err)
