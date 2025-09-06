from typing import Any, Dict
import javalang


def enhancedtree_to_json(tree: javalang.tree.CompilationUnit) -> Dict[str, Any]:
    def extract_type(t):
        # try to get readable name, fall back to str()
        if t is None:
            return None
        if hasattr(t, 'name'):
            # include dimensions if present (array)
            name = t.name
            if getattr(t, 'dimensions', None):
                name += '[]' * len(t.dimensions)
            # include type arguments minimally if present
            if getattr(t, 'arguments', None):
                args = [getattr(a, 'type', str(a)) for a in t.arguments]
                name += f"<{', '.join(map(str, args))}>"
            return name
        return str(t)

    def extract_annotations(node):
        anns = []
        for a in getattr(node, 'annotations', []) or []:
            try:
                anns.append(str(a.name))
            except Exception:
                anns.append(str(a))
        return anns

    def get_position(node):
        pos = getattr(node, 'position', None)
        return pos.line if pos and getattr(pos, 'line', None) else None

    ast = {
        "package": tree.package.name if tree.package else None,
        "imports": [imp.path for imp in tree.imports],
        "classes": []
    }

    for type_decl in tree.types:
        if isinstance(type_decl, javalang.tree.ClassDeclaration):
            cls = {
                "class_name": type_decl.name,
                "modifiers": list(type_decl.modifiers) if getattr(type_decl, 'modifiers', None) else [],
                "annotations": extract_annotations(type_decl),
                "position": get_position(type_decl)
            }

            # superclass and interfaces
            cls["extends"] = extract_type(type_decl.extends) if getattr(type_decl, 'extends', None) else None
            if getattr(type_decl, 'implements', None):
                cls["implements"] = [extract_type(i) for i in type_decl.implements]

            # Fields
            fields = []
            for field in type_decl.fields:
                field_type = extract_type(field.type)
                field_mods = list(field.modifiers) if getattr(field, 'modifiers', None) else []
                for decl in field.declarators:
                    initializer = None
                    if getattr(decl, 'initializer', None) is not None:
                        initializer = str(decl.initializer)
                    fields.append({
                        "name": decl.name,
                        "type": field_type,
                        "modifiers": field_mods,
                        "annotations": extract_annotations(field),
                        "initializer": initializer,
                        "position": get_position(field)
                    })
            if fields:
                cls["fields"] = fields

            # Constructors
            constructors = []
            for ctor in type_decl.constructors:
                constructors.append({
                    "parameters": [
                        {
                          "name": param.name,
                          "type": extract_type(param.type),
                          "annotations": extract_annotations(param),
                          "varargs": getattr(param, 'varargs', False)
                        }
                        for param in ctor.parameters
                    ],
                    "modifiers": list(ctor.modifiers) if getattr(ctor, 'modifiers', None) else [],
                    "throws": [extract_type(t) for t in getattr(ctor, 'throws', [])] if getattr(ctor, 'throws', None) else [],
                    "annotations": extract_annotations(ctor),
                    "position": get_position(ctor)
                })
            if constructors:
                cls["constructors"] = constructors

            # Methods
            methods = []
            for method in type_decl.methods:
                method_json = {
                    "name": method.name,
                    "modifiers": list(method.modifiers) if getattr(method, 'modifiers', None) else [],
                    "visibility": next((m for m in method.modifiers if m in ("public", "protected", "private")), None),
                    "is_static": "static" in method.modifiers if getattr(method, 'modifiers', None) else False,
                    "return_type": extract_type(method.return_type) if method.return_type else "void",
                    "parameters": [
                        {
                          "name": param.name,
                          "type": extract_type(param.type),
                          "annotations": extract_annotations(param),
                          "varargs": getattr(param, 'varargs', False)
                        }
                        for param in method.parameters
                    ],
                    "throws": [extract_type(t) for t in getattr(method, 'throws', [])] if getattr(method, 'throws', None) else [],
                    "annotations": extract_annotations(method),
                    "position": get_position(method)
                }

                # Method Invocations
                invocations = []
                for _, node in method.filter(javalang.tree.MethodInvocation):
                    invocations.append({
                        "qualifier": getattr(node, 'qualifier', None),
                        "member": getattr(node, 'member', None),
                        "arguments": [
                            # try to provide a compact representative string for args
                            (str(arg.member) if isinstance(arg, javalang.tree.MemberReference) else str(arg))
                            for arg in getattr(node, 'arguments', []) or []
                        ],
                        "position": get_position(node)
                    })
                if invocations:
                    method_json["invocations"] = invocations

                # If Statements (simple)
                conditionals = []
                for _, node in method.filter(javalang.tree.IfStatement):
                    conditionals.append({
                        "condition": str(node.condition),
                        "has_else": node.else_statement is not None,
                        "position": get_position(node)
                    })
                if conditionals:
                    method_json["conditionals"] = conditionals

                # Return statements (helps know early-return branches)
                returns = []
                for _, node in method.filter(javalang.tree.ReturnStatement):
                    returns.append({
                        "expression": str(node.expression) if getattr(node, 'expression', None) else None,
                        "position": get_position(node)
                    })
                if returns:
                    method_json["returns"] = returns

                methods.append(method_json)

            if methods:
                cls["methods"] = methods

            # nested types (if any)
            nested = []
            for nested_type in getattr(type_decl, 'body', []) or []:
                # body contains many constructs, but we only record nested type declarations
                if isinstance(nested_type, javalang.tree.ClassDeclaration):
                    nested.append(nested_type.name)
            if nested:
                cls["nested_classes"] = nested

            ast["classes"].append(cls)

    return ast
