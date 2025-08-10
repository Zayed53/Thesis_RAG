from typing import List, Optional
import re

def simple_fix_imports(
    test_code: str,
    package_name: Optional[str],
    source_imports: Optional[List[str]],
    class_name: str
):
    """
    - Removes 'package' line
    - Keeps original test imports
    - Adds class import (if package is provided) and source file imports
    - Ensures JUnit 5 assertion and annotation imports are present
    - Adds additional JUnit 5 imports based on annotation usage
    - Deduplicates all imports
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

    # Always-needed JUnit 5 base imports
    required_base_imports = {
        "import static org.junit.jupiter.api.Assertions.*;",
        "import org.junit.jupiter.api.*;"
    }

    # JUnit 5 annotations with their required imports
    annotation_imports = {
        "@Test": "import org.junit.jupiter.api.Test;",
        "@BeforeEach": "import org.junit.jupiter.api.BeforeEach;",
        "@AfterEach": "import org.junit.jupiter.api.AfterEach;",
        "@BeforeAll": "import org.junit.jupiter.api.BeforeAll;",
        "@AfterAll": "import org.junit.jupiter.api.AfterAll;",
        "@DisplayName": "import org.junit.jupiter.api.DisplayName;",
        "@Disabled": "import org.junit.jupiter.api.Disabled;",
        "@Nested": "import org.junit.jupiter.api.Nested;",
        "@Tag": "import org.junit.jupiter.api.Tag;",
        "@ParameterizedTest": "import org.junit.jupiter.params.ParameterizedTest;",
        "@CsvSource": "import org.junit.jupiter.params.provider.CsvSource;",
        "@ValueSource": "import org.junit.jupiter.params.provider.ValueSource;",
    }

    # Find which annotations are used in code
    used_annotations = {
        annotation for annotation in annotation_imports
        if re.search(rf"\s*{re.escape(annotation)}\b", test_code)
    }

    # Collect needed imports for used annotations
    annotation_needed_imports = {
        annotation_imports[ann] for ann in used_annotations
    }

    # Prepare new imports
    new_imports = []  # start with existing ones

    if package_name:
        new_imports.append(f"import {package_name}.{class_name};")
    if source_imports:
        new_imports += [f"import {imp};" for imp in source_imports]


    # Sort and format
    final_imports = sorted(set(new_imports+ list(required_base_imports)+ list(annotation_needed_imports)))

    return "\n".join(final_imports + [""] + code_body)

# def test_driver():
#     input_code = """package com.example.tests;

# import org.junit.jupiter.api.Test;
# import java.util.List;

# public class MyTest {

#     @Test
#     void sampleTest() {
#         // Some test code
#     }

#     @BeforeEach
#     void setup() {
#         // Setup code
#     }
# }
# """

#     package_name = "com.example"
#     source_imports = ["java.util.ArrayList", "java.util.HashMap"]
#     class_name = "MyClass"

#     fixed_code = simple_fix_imports(input_code, package_name, source_imports, class_name)

#     print("=== Fixed Code ===")
#     print(fixed_code)

#     with open("fixed_test_code.txt", "w") as f:
#         f.write(fixed_code)

#     print("\n✅ Output written to 'fixed_test_code.txt'")

# # Run the test driver
# if __name__ == "__main__":
#     test_driver()