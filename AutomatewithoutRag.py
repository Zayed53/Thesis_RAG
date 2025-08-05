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
Below is a JSON array of method‐metadata for the class under test. Your task is to generate a complete, idiomatic JUnit 5 unit test class for each following Java method:
```json
{json_tree_str}
```
Rules:
- Use @Test from JUnit 5.
- Resolve all the dependencies. Use Mockito (@Mock, Mockito.when(...), verify(...)) for all dependencies.
- Use @BeforeEach for setting up required preconditions before each test method And @AfterEach for cleanup. Use @BeforeAll (static) if setup is required once before all tests.
- Instantiate the class under test using proper constructor.
- For each invocation:
Stub its behavior (when(mock.member(args)).thenReturn(...) for non-void; doNothing().when(...) and verify mehtod call for void ).
- Use Arrange-Act-Assert format.
  -Arrange: Set up inputs, mocks, or stubs.
  -Act: Call the method under test.
  -Assert:  Verify the results.
- Make all test methods public.
- Import only what’s necessary: JUnit 5, Mockito, and the class under test.
- Return only a complete Java test class, no explanation.
- Return Only Code in Response, no other text.
"""
# Use only Ollama (no RAG)
# ...existing code...

# Use only Ollama (no RAG)
    response = ollama.generate(model="codellama", prompt=prompt)
    java_test_code = response['response']

    print("Generated JUnit test cases successfully. Now saving to file...")
    return java_test_code , package, imports
    # with open("Test4.java", "w", encoding="utf-8") as f:
    #     f.write(java_test_code)

    # print("JUnit test cases saved to Test3.java")
