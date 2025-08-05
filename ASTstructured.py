import javalang
import json
from typing import Dict, Any, List


def tree_to_json(tree: javalang.tree.CompilationUnit) -> Dict[str, Any]:
    def extract_type(t):
        return t.name if hasattr(t, 'name') else str(t)

    ast = {
        "package": tree.package.name if tree.package else None,
        "imports": [imp.path for imp in tree.imports],
        "classes": []
    }

    for type_decl in tree.types:
        if isinstance(type_decl, javalang.tree.ClassDeclaration):
            cls = {
                "class_name": type_decl.name,
                "modifiers": list(type_decl.modifiers)
            }

            # Fields
            fields = []
            for field in type_decl.fields:
                field_type = extract_type(field.type)
                for decl in field.declarators:
                    fields.append({
                        "name": decl.name,
                        "type": field_type
                    })
            if fields:
                cls["fields"] = fields

            # Constructors
            constructors = []
            for ctor in type_decl.constructors:
                constructors.append({
                    "parameters": [
                        {"name": param.name, "type": extract_type(param.type)}
                        for param in ctor.parameters
                    ],
                    "modifiers": list(ctor.modifiers)
                })
            if constructors:
                cls["constructors"] = constructors

            # Methods
            methods = []
            for method in type_decl.methods:
                method_json = {
                    "name": method.name,
                    "modifiers": list(method.modifiers),
                    "return_type": extract_type(method.return_type) if method.return_type else "void",
                    "parameters": [
                        {"name": param.name, "type": extract_type(param.type)}
                        for param in method.parameters
                    ]
                }

                # Method Invocations
                invocations = []
                for _, node in method.filter(javalang.tree.MethodInvocation):
                    invocations.append({
                        "qualifier": node.qualifier,
                        "member": node.member,
                        "arguments": [
                            str(arg.member) if isinstance(arg, javalang.tree.MemberReference) else str(arg)
                            for arg in node.arguments
                        ]
                    })
                if invocations:
                    method_json["invocations"] = invocations

                # If Statements
                conditionals = []
                for _, node in method.filter(javalang.tree.IfStatement):
                    conditionals.append({
                        "condition": str(node.condition),
                        "has_else": node.else_statement is not None
                    })
                if conditionals:
                    method_json["conditionals"] = conditionals

                methods.append(method_json)

            if methods:
                cls["methods"] = methods

            ast["classes"].append(cls)

            

    return ast


# Example usage
# if __name__ == "__main__":
#     java_code = """
#     public class OrderProcessor {
#         private PaymentService paymentService;
#         private InventoryService inventoryService;

#         public OrderProcessor(PaymentService paymentService, InventoryService inventoryService) {
#             this.paymentService = paymentService;
#             this.inventoryService = inventoryService;
#         }

#         public boolean processOrder(String orderId) {
#             boolean paymentSuccess = paymentService.charge(orderId);
#             if (!paymentSuccess) {
#                 return false;
#             }
#             inventoryService.reserveItems(orderId);
#             return true;
#         }

#         public void cancelOrder(String orderId) {
#             paymentService.refund(orderId);
#             inventoryService.releaseItems(orderId);
#         }

#         public String getOrderStatus(String orderId) {
#             return "Processed";
#         }
#     }
#     """

#     tree = javalang.parse.parse(java_code)
#     json_tree = tree_to_json(tree)
#     print(json.dumps(json_tree, indent=2))
