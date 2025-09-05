import os
import json
from typing import List, Dict

def discover_maven_projects(root_folder: str,
                            json_out: str = "projects_list.json",
                            require_test_dir: bool = False) -> List[Dict[str, str]]:
    """
    Scan `root_folder` recursively and return a list of projects found.
    Each project is a dict with keys:
      - "src_path"   : absolute path to <project_root>/src/main/java
      - "output_dir" : absolute path to <project_root>/src/test/java

    If require_test_dir is True, only include projects where src/test/java exists.
    Writes the list to `json_out` and also returns it.
    """
    root_folder = os.path.abspath(root_folder)
    projects = []
    seen_roots = set()

    for dirpath, dirnames, filenames in os.walk(root_folder):
        # skip hidden folders (optional)
        rel = os.path.relpath(dirpath, root_folder)
        if rel != "." and any(part.startswith('.') for part in rel.split(os.sep)):
            continue

        # If this dir is already inside a discovered project root, skip
        # (prevents nested duplicates)
        if any(dirpath.startswith(r + os.sep) or dirpath == r for r in seen_roots):
            continue

        main_java = os.path.join(dirpath, "src", "main", "java")
        test_java = os.path.join(dirpath, "src", "test", "java")

        # Found a project root candidate if it contains src/main/java
        if os.path.isdir(main_java):
            # If require_test_dir, ensure src/test/java exists
            if require_test_dir and not os.path.isdir(test_java):
                # skip this one (test missing)
                continue

            entry = {
                "src_path": os.path.abspath(main_java),
                "output_dir": os.path.abspath(test_java)
            }
            projects.append(entry)

            # Mark this dir as discovered project root and skip walking deeper into it
            seen_roots.add(os.path.abspath(dirpath))
            # prevent os.walk from going into subdirs of this project root
            dirnames[:] = []
            continue

    # write JSON
    with open(json_out, "w", encoding="utf-8") as jf:
        json.dump(projects, jf, indent=2, ensure_ascii=False)

    return projects
