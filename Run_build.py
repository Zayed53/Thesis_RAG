import datetime
import subprocess
import re
import os
import json


project_path = r"F:\Thesis_SELAB_PMT\java_project\apollo"
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

