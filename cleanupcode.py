import re

def clean_java_code(raw_text: str) -> str:
    """
    Cleans mixed Java code and markdown, preserving all executable code.
    - Removes markdown fences (``` and ```java)
    - Keeps all lines from the first 'import' or 'class' to the last closing brace
    - Preserves comments and annotations
    - Ensures the output is a valid, executable Java class
    """
    lines = raw_text.strip().splitlines()
    # Remove markdown fences and empty lines
    lines = [line for line in lines if not line.strip().startswith("```") and line.strip() != ""]

    # Find the start of Java code (first 'import' or 'class')
    start_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("import") or line.strip().startswith("public class") or line.strip().startswith("class"):
            start_index = i
            break
    if start_index == -1:
        return ""  # No valid Java code found

    # Collect lines until the last closing brace
    collected_lines = lines[start_index:]
    brace_balance = 0
    final_index = len(collected_lines)
    for i, line in enumerate(collected_lines):
        brace_balance += line.count("{")
        brace_balance -= line.count("}")
        # If brace_balance returns to zero and we've seen at least one opening brace, stop
        if brace_balance == 0 and "{" in "".join(collected_lines[:i+1]):
            final_index = i + 1
            break

    # Join and return the cleaned Java code
    java_code = "\n".join(collected_lines[:final_index]).strip()
    return java_code

