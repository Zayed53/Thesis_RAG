import javalang
from typing import Dict, Any, List


def extract_all_methods_metadata(java_code: str) -> List[Dict[str, Any]]:
    tree = javalang.parse.parse(java_code)
    print("Tree:", tree)
    results = []

    class_decl = next(iter(tree.types), None)
    if not isinstance(class_decl, javalang.tree.ClassDeclaration):
        return results

    focal_class = class_decl.name

    # Map fields to their types (to resolve injected services)
    field_types = {}
    for field in class_decl.fields:
        field_type = field.type.name
        for decl in field.declarators:
            field_types[decl.name] = field_type

    for method in class_decl.methods:
        result = {
            "focal_class": focal_class,
            "method_name": method.name,
            "parameters": [],
            "return_type": method.return_type.name if method.return_type else "void",
            "dependencies": [],
            "invocations": []
        }

        param_names = {param.name for param in method.parameters}
        for param in method.parameters:
            result["parameters"].append(f"{param.type.name} {param.name}")

        local_vars = set(param_names)
        for _, node in method.filter(javalang.tree.VariableDeclarator):
            local_vars.add(node.name)

        dependencies = set()
        invocations = []

        for _, node in method.filter(javalang.tree.MethodInvocation):
            if node.qualifier and node.qualifier not in local_vars:
                dependencies.add(node.qualifier)
                invocations.append({
                    "member": node.member,
                    "qualifier": node.qualifier,
                    "arguments": [arg.member if isinstance(arg, javalang.tree.MemberReference) else str(arg.value) for arg in node.arguments or []]
                })

        result["dependencies"] = list({field_types.get(dep, dep) for dep in dependencies})
        result["invocations"] = invocations

        results.append(result)

    return results


# Example usage
if __name__ == "__main__":
    JAVA_CODE = """
    public class OrderProcessor {

        public boolean processOrder(String orderId) {
            boolean paymentSuccess = paymentService.charge(orderId);
            if (!paymentSuccess) {
                return false;
            }
            inventoryService.reserveItems(orderId);
            return true;
        }

        public void cancelOrder(String orderId) {
            paymentService.refund(orderId);
            inventoryService.releaseItems(orderId);
        }

        public String getOrderStatus(String orderId) {
            return "Processed";
        }
    }
    """

    import json
    metadata = extract_all_methods_metadata(JAVA_CODE)
    print(json.dumps(metadata, indent=2))
