from typing import List


from typing import List, Optional

def simple_fix_imports(
    test_code: str,
    package_name: Optional[str],
    source_imports: Optional[List[str]],
    class_name: str
) :
    """
    - Removes 'package' line
    - Keeps original test imports
    - Adds class import (if package is provided) and source file imports
    - Deduplicates all imports
    - Does nothing if both package_name and source_imports are empty
    """
    if not package_name and not source_imports:
        return test_code  # Nothing to fix

    lines = test_code.splitlines()

    # Extract existing imports
    original_imports = [
        line.strip() for line in lines
        if line.strip().startswith("import")
    ]

    # Remove package and import lines
    code_body = [
        line for line in lines
        if not line.strip().startswith("package")
        and not line.strip().startswith("import")
    ]

    # Prepare new imports
    new_imports = []
    if package_name:
        new_imports.append(f"import {package_name}.{class_name};")
    if source_imports:
        new_imports += [f"import {imp};" for imp in source_imports]

    # Combine and deduplicate
    all_imports = sorted(set(original_imports + new_imports))

    # Final output
    return "\n".join(all_imports + [""] + code_body)
