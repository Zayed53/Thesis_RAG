import os
from AutomateRag import GenerateTest
from AutomatewithoutRag import GenerateTestWithoutRag
from cleanupcode import clean_java_code
from fix_imports import simple_fix_imports

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
                    test_code, package, imports = GenerateTestWithoutRag(str(java_code))
                    cleaned_test_code = clean_java_code(test_code)
                    import_fixed_test_code = simple_fix_imports(
                        cleaned_test_code,
                        package,
                        imports,
                        os.path.splitext(file)[0]  )
                    # Prepare output path
                    test_file_name = os.path.splitext(file)[0] + "tTest.java"
                    # test_file_rel_dir = os.path.dirname(rel_path)
                    # test_file_dir = os.path.join(output_dir, test_file_rel_dir)
                    test_file_dir = output_dir
                    os.makedirs(test_file_dir, exist_ok=True)
                    test_file_path = os.path.join(test_file_dir, test_file_name)
                    with open(test_file_path, 'w', encoding='utf-8') as out:
                        out.write(import_fixed_test_code)
                except Exception as e:
                    print(f"Error processing {abs_path}: {e}")

if __name__ == "__main__":
    src_path = r"C:\Users\alico\Documents\SDA_LAB\UnitTestMaven\src\main\java"
    output_dir = r"C:\Users\alico\Documents\SDA_LAB\UnitTestMaven\src\test\java"
    collect_java_files(src_path, output_dir)
    print(f"Processed Java files. Test files written to {output_dir}")