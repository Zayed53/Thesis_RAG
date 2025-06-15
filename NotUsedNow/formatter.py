import ollama
import json


result = {
    "language": None,
    "test_framework": None,
    "dependencies": [],             # list of helper functions / classes
    "metadata": {},                  # e.g. params, types, docstring hints
    "keywords": {
        "arrange": [],
        "act": [],
        "assert": []
    },
    "enhanced_prompt": ""
}

system_prompt = """
You are an expert code analyzer.

Extract the following structured JSON from the given method or function. This information will help scaffold unit tests:

{
  "language": (Detect the programming language),
  "test_framework": (Best test framework for this language, e.g., 'pytest', 'unittest', 'JUnit'),
  "dependencies": (Classes, services, or methods this method relies on),
  "metadata": {
    "parameters": (list of parameter names with types if available),
    "return_type": (return type of the method),
    "summary": (summary of method behavior based on docstring or logic)
  },
  
  "focal_class": (Name of the class this method belongs to, if any)
}

Respond with only the valid JSON. Do not explain or wrap it in markdown or text.
"""

method_input = """
public class BusinessLogic {
    private DoService doService;

    public void deleteTodosNotRelatedToHibernate(String user) {
        List<String> Combinedlist = doService.getTodos(user);
        for (String todos : Combinedlist) {
            if (!todos.contains("Hibernate")) {
                doService.deleteTodos(todos);
            }
        }
    }
}
"""

prompt = f"{system_prompt}\n\n{method_input}"


# response = ollama.chat(model="codellama", messages=[
#         {"role": "user", "content": prompt}
#     ])
print("************/////////Model RUnning Start/////////*********")
response = ollama.generate(model="codellama", prompt=prompt)

# try:
#     parsed = json.loads(response["message"]["content"])
#     print("Response:", parsed)
# except json.JSONDecodeError:
#     print("Failed to parse model response:")
#     print(response["message"]["content"])
#     print( {
#         "language": None,
#         "test_framework": None,
#         "dependencies": [],
#         "metadata": {},
#         "keywords": {
#             "arrange": [],
#             "act": [],
#             "assert": []
#         },
#         "focal_class": ""
#     })
try:
    parsed = json.loads(response["response"])
    print(json.dumps(parsed, indent=4))
except json.JSONDecodeError:
    print(json.dumps({
        "language": None,
        "test_framework": None,
        "dependencies": [],
        "metadata": {},
        "keywords": {
            "arrange": [],
            "act": [],
            "assert": []
        },
        "focal_class": ""
    }, indent=4))