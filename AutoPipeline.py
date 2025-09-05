import os
from AutomateRag import GenerateTest
from AutomatewithoutRag import GenerateTestWithoutRag
from cleanupcode import clean_java_code
from discover_Projects import discover_maven_projects
from fix_imports import simple_fix_imports
import javalang
import re
import json

results = {
        "Processed_files": 0,
        "generated_tests_classes": 0,
        "Error_Count": 0,
        "errors": [],
        "ProjectCount":0,
        "lastProject":{}
    }

# def has_public_class(java_code: str) -> bool:
#     try:
#         tree = javalang.parse.parse(java_code)
#         for type_decl in tree.types:
#             if isinstance(type_decl, javalang.tree.ClassDeclaration):
#                 if "public" in type_decl.modifiers:
#                     return True
#         return False
#     except:
#         return False

def has_interface_or_enum(java_code: str) -> bool:
    try:
        tree = javalang.parse.parse(java_code)
        for type_decl in tree.types:
            # Check if it's an interface
            if isinstance(type_decl, javalang.tree.InterfaceDeclaration):
                return True
            # Check if it's an enum
            if isinstance(type_decl, javalang.tree.EnumDeclaration):
                return True
        return False
    except:
        return False
    

def collect_java_files(src_path, output_dir):
    
    for root, dirs, files in os.walk(src_path):
        for file in files:
            if file.endswith('.java'):
                print(f"Processing {file} in {root}")
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, src_path)
                try:
                    with open(abs_path, 'r', encoding='utf-8') as java_file:
                        java_code = java_file.read()
                    if has_interface_or_enum(java_code):
                        print(f"Skipping {file} — no public class found.")
                        continue
                    results["Processed_files"] += 1
                    test_code, package, imports = GenerateTestWithoutRag(str(java_code))
                    cleaned_test_code = clean_java_code(test_code)
                    import_fixed_test_code = simple_fix_imports(
                        cleaned_test_code,
                        package,
                        imports,
                        os.path.splitext(file)[0]  )
                    
                    # Prepare output path
                    match = re.search(r'public\s+class\s+([A-Za-z_]\w*)', import_fixed_test_code)
                    if match:
                        test_class_name = match.group(1)
                        test_file_name = test_class_name + ".java"
                    else:
                        match2 = re.search(r'\bclass\s+([A-Za-z_]\w*)', import_fixed_test_code)

                        if match2:
                            test_class_name = match2.group(1)
                            test_file_name = test_class_name + ".java"
                        else:
                            test_file_name = os.path.splitext(os.path.basename(file))[0] + "Test.java"

                    # convert package (com.example.demo) -> path (com/example/demo)
                    if package:
                        test_file_rel_dir = package.replace(".", os.sep)
                    else:
                        test_file_rel_dir = ""

                    # combine output_dir with package path
                    test_file_dir = os.path.join(output_dir, test_file_rel_dir)
                    os.makedirs(test_file_dir, exist_ok=True)

                    # final test file path
                    test_file_path = os.path.join(test_file_dir, test_file_name)
                    results["generated_tests_classes"] += 1
                    with open(test_file_path, 'w', encoding='utf-8') as out:
                        out.write(import_fixed_test_code)
                except Exception as e:
                    print(f"Error processing {abs_path}: {e}")
                    results["Error_Count"] += 1
                    results["errors"].append({
                        "file": abs_path,
                        "error": str(e)
                    })

# if __name__ == "__main__":
#     src_path = r"f:\Thesis_SELAB_PMT\Projects\bank-application\src\com\youtube\bank"
#     output_dir = r"f:\Thesis_SELAB_PMT\Projects\bank-application\src\second\test\java"
#     collect_java_files(src_path, output_dir)
#     print(f"Processed Java files. Test files written to {output_dir}")


if __name__ == "__main__":
    # 🔹 Define multiple projects in a list (dict-like JSON structure)

        
        # 👉 You can add more projects here
    
    #######change here for re Run or new Run ##############################

    ############# Use the following for new run#######################

    root = r"F:\MavenJavaProjectsFromGithub_deepseek_AST"  
    projects = discover_maven_projects(root, json_out="projects_list_For_src_MavenJavaProjectsFromGithub_deepseek_AST.json", require_test_dir=True)
    ################Use this for reRun#########################
    # srcpath="F:\\Thesis_SELAB_PMT\\PROJECTS_ALL - Maven - CodeLLama_AST_Run2\\tutorials\\jackson-modules\\jackson-conversions-2\\src\\main\\java"
    # srcpath="F:\\Thesis_SELAB_PMT\\PROJECTS_ALL - Maven - CodeLLama_AST_Run2\\tutorials\\spring-cloud-modules\\spring-cloud-archaius\\spring-cloud-archaius-additionalsources\\src\\main\\java\\com\\baeldung\\spring\\cloud\\archaius\\additionalsources\\AdditionalSourcesSimpleApplication.java"
    # srcpath="F:\\Thesis_SELAB_PMT\\java_project - Copy_Codellama\\commons-math\\commons-math-core\\src\\main\\java"
    # srcpath="F:\\Thesis_SELAB_PMT\\java_project -copy-deepseek\\apollo\\apollo-adminservice\\src\\main\\java"
    # with open("projects_list_For_srcodellama_Javacode.json", "r", encoding="utf-8") as f:
    #     projects = json.load(f)
    
    # start_index = next((i for i, project in enumerate(projects) if project["src_path"] == srcpath), None)

    # if start_index is None:
    #     print("No such project found")
    #     exit(0)
    # print(len(projects))
    # projects = projects[start_index:]
    totalporject=len(projects)
    print(totalporject)
    # 🔹 Run collection for each project
    currentrun=0
    for project in projects: 
        if(currentrun>400):
            break
        print(f"\n=== Processing project: {project['src_path']} ===")
        collect_java_files(project["src_path"], project["output_dir"])
        print(f"✅ Processed. Test files written to {project['output_dir']}")
        results["ProjectCount"] +=1
        results["lastProject"] = {
            "srcpath": project["src_path"],
            "output": project["output_dir"]
        }
        print(f"\n=== Remaining: {totalporject-results["ProjectCount"]} ===")
        with open("recordsData_MavenJavaProjectsFromGithub_deepseek_AST.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        
        currentrun+=1
    
    
    
