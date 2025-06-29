import subprocess
import os

SRC_DIR = "../src"
MAIN_SRC = os.path.join(SRC_DIR, "main")
TEST_SRC = os.path.join(SRC_DIR, "test")
BIN_DIR = "../bin"
LIB_DIR = "../lib"
JUNIT_JAR = os.path.join(LIB_DIR, "junit-platform-console-standalone-1.10.2.jar")

os.makedirs(BIN_DIR, exist_ok=True)

def collect_java_files(directory):
    java_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".java"):
                java_files.append(os.path.join(root, file))
    return java_files

def compile_java():
    # main_files = collect_java_files(MAIN_SRC)
    test_files = collect_java_files(TEST_SRC)
    all_files =  test_files
    cmd = ["javac", "-cp", JUNIT_JAR, "-d", BIN_DIR] + all_files
    subprocess.run(cmd, check=True)
    print("✅ Compilation completed")

def run_tests():
    cmd = [
        "java",
        "-jar", JUNIT_JAR,
        "-cp", BIN_DIR,
        "--scan-class-path",
        "--reports-dir=../reports"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    return result.stdout

if __name__ == "__main__":
    compile_java()
    output = run_tests()

    if "SUCCESSFUL" in output and "0 tests" not in output:
        print("✅ All tests passed")
    else:
        print("❌ Some tests failed or were not detected")
