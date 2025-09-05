import json
import os
import shutil

# path to your error JSON
json_file = "compile_report.json"

# target folder for broken classes
broken_dir = "broken_tests"

with open(json_file, "r") as f:
    data = json.load(f)

# ensure the broken_tests folder exists
os.makedirs(broken_dir, exist_ok=True)

# keep track of unique files
moved_files = set()

for error in data["errors"]:
    file_path = error["file"].lstrip("/")  # remove leading "/" from your JSON paths
    if file_path not in moved_files and os.path.exists(file_path):
        moved_files.add(file_path)

        # preserve original folder structure (optional)
        relative_path = os.path.relpath(file_path, data["project"])
        dest_path = os.path.join(broken_dir, relative_path)

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.move(file_path, dest_path)

        print(f"Moved: {file_path} → {dest_path}")

print(f"\n✅ Moved {len(moved_files)} broken files to {broken_dir}")
