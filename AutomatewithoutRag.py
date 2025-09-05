# ...existing code...
import ollama
from ASTstructured import tree_to_json
import javalang
import json
from Data import *
# ...existing code...

# Prepare your Java source code

def GenerateTestWithoutRag(sourceCode):
    tree = javalang.parse.parse(sourceCode)
    json_tree = tree_to_json(tree)
    json_tree_str = json.dumps(json_tree, indent=2)

    package = json_tree['package']
    imports = json_tree['imports']

    prompt = f"""	
You are a Java testing assistant.
Below is the Abstract Syntaxt Tree of a java class. Your task is to generate a complete, idiomatic JUnit 5 unit test class for each Public Java method in the class:
```
{json_tree_str}
```
Rules:
- Use @Test from JUnit 5.
- Create Test for Public method Only.
- Test Class name will end with "ClassunderTest"+Test.
- Resolve the dependencies.
- Instantiate the class under test using proper constructor.
- Use Arrange-Act-Assert format.
- Make all test methods public.
- Make the test class public.
- Import only what is necessary.
- Return only a complete Java test class, no explanation.
- Return Only Code in Response, no other text.
"""
# Use only Ollama (no RAG)
# ...existing code...

# Use only Ollama (no RAG)
    # response = ollama.generate(model="codellama", prompt=prompt)
    response = ollama.generate(model="deepseek-coder", prompt=prompt)
    java_test_code = response['response']

    print("Generated JUnit test cases successfully. Now saving to file...")
    return java_test_code , package, imports
    # with open("Test4.java", "w", encoding="utf-8") as f:
    #     f.write(java_test_code)

    # print("JUnit test cases saved to Test3.java")
