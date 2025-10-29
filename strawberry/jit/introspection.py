"""Introspection selection generation for JIT compiler.

This module contains the introspection query handling logic extracted from the main
JIT compiler to improve code organization and maintainability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from graphql import (
    FieldNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    SelectionSetNode,
)

if TYPE_CHECKING:
    from strawberry.jit import JITCompiler


def generate_introspection_selection(
    compiler: JITCompiler,
    selection_set: SelectionSetNode,
    introspection_type: str,
    parent_var: str,
    result_var: str,
    info_var: str,
    path: str,
) -> None:
    """Generate selection for introspection types (__Schema, __Type, etc)."""
    # Map introspection type names to their field resolvers
    introspection_resolvers = {
        "__Schema": {
            "queryType": lambda schema: schema.query_type,
            "mutationType": lambda schema: schema.mutation_type,
            "subscriptionType": lambda schema: schema.subscription_type,
            "types": lambda schema: list(schema.type_map.values()),
            "directives": lambda schema: schema.directives,
        },
        "__Type": {
            "kind": lambda t: compiler._get_type_kind(t),
            "name": lambda t: t.name if hasattr(t, "name") else None,
            "description": lambda t: t.description
            if hasattr(t, "description")
            else None,
            "fields": lambda t: list(t.fields.values())
            if hasattr(t, "fields")
            else None,
            "interfaces": lambda t: list(t.interfaces)
            if hasattr(t, "interfaces")
            else None,
            "possibleTypes": lambda t: list(t.types) if hasattr(t, "types") else None,
            "enumValues": lambda t: list(t.values.values())
            if hasattr(t, "values")
            else None,
            "inputFields": lambda t: list(t.fields.values())
            if hasattr(t, "fields")
            else None,
            "ofType": lambda t: t.of_type if hasattr(t, "of_type") else None,
        },
        "__Field": {
            "name": lambda f: f.name,
            "description": lambda f: f.description,
            "args": lambda f: list(f.args.values()) if f.args else [],
            "type": lambda f: f.type,
            "isDeprecated": lambda f: f.deprecation_reason is not None,
            "deprecationReason": lambda f: f.deprecation_reason,
        },
        "__InputValue": {
            "name": lambda i: i.name if hasattr(i, "name") else None,
            "description": lambda i: i.description
            if hasattr(i, "description")
            else None,
            "type": lambda i: i.type if hasattr(i, "type") else None,
            "defaultValue": lambda i: str(i.default_value)
            if hasattr(i, "default_value") and i.default_value is not None
            else None,
        },
        "__EnumValue": {
            "name": lambda e: e.value,
            "description": lambda e: e.description,
            "isDeprecated": lambda e: e.deprecation_reason is not None,
            "deprecationReason": lambda e: e.deprecation_reason,
        },
        "__Directive": {
            "name": lambda d: d.name,
            "description": lambda d: d.description,
            "locations": lambda d: d.locations,
            "args": lambda d: list(d.args.values()) if d.args else [],
        },
    }

    for selection in selection_set.selections:
        # Handle fragment spreads in introspection
        if isinstance(selection, FragmentSpreadNode):
            fragment_name = selection.name.value
            if fragment_name in compiler.fragments:
                fragment_def = compiler.fragments[fragment_name]
                # Check type condition matches
                if fragment_def.type_condition.name.value == introspection_type:
                    compiler._emit(f"# Fragment spread: {fragment_name}")
                    generate_introspection_selection(
                        compiler,
                        fragment_def.selection_set,
                        introspection_type,
                        parent_var,
                        result_var,
                        info_var,
                        path,
                    )
            continue

        # Handle inline fragments in introspection
        if isinstance(selection, InlineFragmentNode):
            if selection.type_condition:
                if selection.type_condition.name.value == introspection_type:
                    compiler._emit(f"# Inline fragment on {introspection_type}")
                    generate_introspection_selection(
                        compiler,
                        selection.selection_set,
                        introspection_type,
                        parent_var,
                        result_var,
                        info_var,
                        path,
                    )
            else:
                # No type condition - always apply
                generate_introspection_selection(
                    compiler,
                    selection.selection_set,
                    introspection_type,
                    parent_var,
                    result_var,
                    info_var,
                    path,
                )
            continue
        if isinstance(selection, FieldNode):
            field_name = compiler._sanitize_identifier(selection.name.value)
            alias = (
                compiler._sanitize_identifier(selection.alias.value)
                if selection.alias
                else field_name
            )

            if field_name == "__typename":
                compiler._emit(f'{result_var}["{alias}"] = "{introspection_type}"')
                continue

            # Generate code to resolve the introspection field
            compiler._emit(f"# Resolve {introspection_type}.{field_name}")

            # Handle special cases for introspection fields
            if introspection_type == "__Schema":
                if field_name == "queryType":
                    compiler._emit(f"schema_query_type = {parent_var}.query_type")
                    if selection.selection_set:
                        compiler._emit("if schema_query_type:")
                        compiler.indent_level += 1
                        compiler._emit(f"{result_var}['{alias}'] = {{}}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__Type",
                            "schema_query_type",
                            f"{result_var}['{alias}']",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler.indent_level -= 1
                        compiler._emit("else:")
                        compiler.indent_level += 1
                        compiler._emit(f"{result_var}['{alias}'] = None")
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = schema_query_type")
                elif field_name == "mutationType":
                    compiler._emit(f"schema_mutation_type = {parent_var}.mutation_type")
                    if selection.selection_set:
                        compiler._emit("if schema_mutation_type:")
                        compiler.indent_level += 1
                        compiler._emit(f"{result_var}['{alias}'] = {{}}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__Type",
                            "schema_mutation_type",
                            f"{result_var}['{alias}']",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler.indent_level -= 1
                        compiler._emit("else:")
                        compiler.indent_level += 1
                        compiler._emit(f"{result_var}['{alias}'] = None")
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(
                            f"{result_var}['{alias}'] = schema_mutation_type"
                        )
                elif field_name == "subscriptionType":
                    compiler._emit(
                        f"schema_subscription_type = {parent_var}.subscription_type"
                    )
                    if selection.selection_set:
                        compiler._emit("if schema_subscription_type:")
                        compiler.indent_level += 1
                        compiler._emit(f"{result_var}['{alias}'] = {{}}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__Type",
                            "schema_subscription_type",
                            f"{result_var}['{alias}']",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler.indent_level -= 1
                        compiler._emit("else:")
                        compiler.indent_level += 1
                        compiler._emit(f"{result_var}['{alias}'] = None")
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(
                            f"{result_var}['{alias}'] = schema_subscription_type"
                        )
                elif field_name == "types":
                    compiler._emit(
                        f"schema_types = list({parent_var}.type_map.values())"
                    )
                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = []")
                        compiler._emit("for schema_type in schema_types:")
                        compiler.indent_level += 1
                        compiler._emit("type_result = {}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__Type",
                            "schema_type",
                            "type_result",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler._emit(f"{result_var}['{alias}'].append(type_result)")
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = schema_types")
                elif field_name == "directives":
                    compiler._emit(f"schema_directives = {parent_var}.directives")
                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = []")
                        compiler._emit("for directive in schema_directives:")
                        compiler.indent_level += 1
                        compiler._emit("directive_result = {}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__Directive",
                            "directive",
                            "directive_result",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler._emit(
                            f"{result_var}['{alias}'].append(directive_result)"
                        )
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = schema_directives")

            elif introspection_type == "__Type":
                if field_name == "kind":
                    compiler._emit(
                        "from graphql.type import is_scalar_type, is_object_type, is_interface_type, is_union_type, is_enum_type, is_input_object_type, is_list_type, is_non_null_type"
                    )
                    compiler._emit(f"if is_scalar_type({parent_var}):")
                    compiler.indent_level += 1
                    compiler._emit(f'{result_var}["{alias}"] = "SCALAR"')
                    compiler.indent_level -= 1
                    compiler._emit(f"elif is_object_type({parent_var}):")
                    compiler.indent_level += 1
                    compiler._emit(f'{result_var}["{alias}"] = "OBJECT"')
                    compiler.indent_level -= 1
                    compiler._emit(f"elif is_interface_type({parent_var}):")
                    compiler.indent_level += 1
                    compiler._emit(f'{result_var}["{alias}"] = "INTERFACE"')
                    compiler.indent_level -= 1
                    compiler._emit(f"elif is_union_type({parent_var}):")
                    compiler.indent_level += 1
                    compiler._emit(f'{result_var}["{alias}"] = "UNION"')
                    compiler.indent_level -= 1
                    compiler._emit(f"elif is_enum_type({parent_var}):")
                    compiler.indent_level += 1
                    compiler._emit(f'{result_var}["{alias}"] = "ENUM"')
                    compiler.indent_level -= 1
                    compiler._emit(f"elif is_input_object_type({parent_var}):")
                    compiler.indent_level += 1
                    compiler._emit(f'{result_var}["{alias}"] = "INPUT_OBJECT"')
                    compiler.indent_level -= 1
                    compiler._emit(f"elif is_list_type({parent_var}):")
                    compiler.indent_level += 1
                    compiler._emit(f'{result_var}["{alias}"] = "LIST"')
                    compiler.indent_level -= 1
                    compiler._emit(f"elif is_non_null_type({parent_var}):")
                    compiler.indent_level += 1
                    compiler._emit(f'{result_var}["{alias}"] = "NON_NULL"')
                    compiler.indent_level -= 1
                    compiler._emit("else:")
                    compiler.indent_level += 1
                    compiler._emit(f'{result_var}["{alias}"] = None')
                    compiler.indent_level -= 1
                elif field_name == "name":
                    compiler._emit(
                        f'{result_var}["{alias}"] = {parent_var}.name if hasattr({parent_var}, "name") else None'
                    )
                elif field_name == "description":
                    compiler._emit(
                        f'{result_var}["{alias}"] = {parent_var}.description if hasattr({parent_var}, "description") else None'
                    )
                elif field_name == "fields":
                    # Get includeDeprecated argument
                    include_deprecated = False
                    if selection.arguments:
                        for arg in selection.arguments:
                            if arg.name.value == "includeDeprecated":
                                arg_val = compiler._generate_argument_value(
                                    arg.value, info_var
                                )
                                compiler._emit(f"include_deprecated = {arg_val}")
                                include_deprecated = True
                                break
                    if not include_deprecated:
                        compiler._emit("include_deprecated = False")

                    compiler._emit(f"if hasattr({parent_var}, 'fields'):")
                    compiler.indent_level += 1
                    compiler._emit("type_fields = []")
                    compiler._emit(
                        f"for field_name, field_def in {parent_var}.fields.items():"
                    )
                    compiler.indent_level += 1
                    compiler._emit(
                        "if include_deprecated or not field_def.deprecation_reason:"
                    )
                    compiler.indent_level += 1
                    compiler._emit("type_fields.append((field_name, field_def))")
                    compiler.indent_level -= 1
                    compiler.indent_level -= 1

                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = []")
                        compiler._emit("for field_name, field_def in type_fields:")
                        compiler.indent_level += 1
                        compiler._emit("field_result = {}")
                        # Pass both field_name and field_def
                        compiler._emit("field_with_name = (field_name, field_def)")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__Field",
                            "field_with_name",
                            "field_result",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler._emit(f"{result_var}['{alias}'].append(field_result)")
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = type_fields")
                    compiler.indent_level -= 1
                    compiler._emit("else:")
                    compiler.indent_level += 1
                    compiler._emit(f"{result_var}['{alias}'] = None")
                    compiler.indent_level -= 1
                elif field_name == "interfaces":
                    compiler._emit(f"if hasattr({parent_var}, 'interfaces'):")
                    compiler.indent_level += 1
                    compiler._emit(f"type_interfaces = list({parent_var}.interfaces)")
                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = []")
                        compiler._emit("for interface in type_interfaces:")
                        compiler.indent_level += 1
                        compiler._emit("interface_result = {}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__Type",
                            "interface",
                            "interface_result",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler._emit(
                            f"{result_var}['{alias}'].append(interface_result)"
                        )
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = type_interfaces")
                    compiler.indent_level -= 1
                    compiler._emit("else:")
                    compiler.indent_level += 1
                    compiler._emit(f"{result_var}['{alias}'] = None")
                    compiler.indent_level -= 1
                elif field_name == "possibleTypes":
                    compiler._emit(f"if hasattr({parent_var}, 'types'):")
                    compiler.indent_level += 1
                    compiler._emit(f"possible_types = list({parent_var}.types)")
                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = []")
                        compiler._emit("for ptype in possible_types:")
                        compiler.indent_level += 1
                        compiler._emit("ptype_result = {}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__Type",
                            "ptype",
                            "ptype_result",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler._emit(f"{result_var}['{alias}'].append(ptype_result)")
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = possible_types")
                    compiler.indent_level -= 1
                    compiler._emit("else:")
                    compiler.indent_level += 1
                    compiler._emit(f"{result_var}['{alias}'] = None")
                    compiler.indent_level -= 1
                elif field_name == "enumValues":
                    # Get includeDeprecated argument
                    include_deprecated = False
                    if selection.arguments:
                        for arg in selection.arguments:
                            if arg.name.value == "includeDeprecated":
                                arg_val = compiler._generate_argument_value(
                                    arg.value, info_var
                                )
                                compiler._emit(f"include_deprecated = {arg_val}")
                                include_deprecated = True
                                break
                    if not include_deprecated:
                        compiler._emit("include_deprecated = False")

                    compiler._emit(f"if hasattr({parent_var}, 'values'):")
                    compiler.indent_level += 1
                    compiler._emit(f"enum_values = list({parent_var}.values.values())")
                    compiler._emit("if not include_deprecated:")
                    compiler.indent_level += 1
                    compiler._emit(
                        "enum_values = [v for v in enum_values if not v.deprecation_reason]"
                    )
                    compiler.indent_level -= 1

                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = []")
                        compiler._emit("for enum_val in enum_values:")
                        compiler.indent_level += 1
                        compiler._emit("enum_result = {}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__EnumValue",
                            "enum_val",
                            "enum_result",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler._emit(f"{result_var}['{alias}'].append(enum_result)")
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = enum_values")
                    compiler.indent_level -= 1
                    compiler._emit("else:")
                    compiler.indent_level += 1
                    compiler._emit(f"{result_var}['{alias}'] = None")
                    compiler.indent_level -= 1
                elif field_name == "inputFields":
                    compiler._emit("from graphql import is_input_object_type")
                    compiler._emit(f"if is_input_object_type({parent_var}):")
                    compiler.indent_level += 1
                    compiler._emit("input_fields = []")
                    compiler._emit(
                        f"for field_name, field_def in {parent_var}.fields.items():"
                    )
                    compiler.indent_level += 1
                    compiler._emit("input_fields.append((field_name, field_def))")
                    compiler.indent_level -= 1

                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = []")
                        compiler._emit("for input_field_tuple in input_fields:")
                        compiler.indent_level += 1
                        compiler._emit("input_result = {}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__InputValue",
                            "input_field_tuple",
                            "input_result",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler._emit(f"{result_var}['{alias}'].append(input_result)")
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = input_fields")
                    compiler.indent_level -= 1
                    compiler._emit("else:")
                    compiler.indent_level += 1
                    compiler._emit(f"{result_var}['{alias}'] = None")
                    compiler.indent_level -= 1
                elif field_name == "ofType":
                    compiler._emit(f"if hasattr({parent_var}, 'of_type'):")
                    compiler.indent_level += 1
                    compiler._emit(f"of_type = {parent_var}.of_type")
                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = {{}}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__Type",
                            "of_type",
                            f"{result_var}['{alias}']",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = of_type")
                    compiler.indent_level -= 1
                    compiler._emit("else:")
                    compiler.indent_level += 1
                    compiler._emit(f"{result_var}['{alias}'] = None")
                    compiler.indent_level -= 1

            elif introspection_type == "__Field":
                # __Field can be either a tuple (field_name, field_def) or just field_def
                compiler._emit("# Handle __Field which may be a tuple")
                compiler._emit(f"if isinstance({parent_var}, tuple):")
                compiler.indent_level += 1
                compiler._emit(f"_field_name, _field_def = {parent_var}")
                compiler.indent_level -= 1
                compiler._emit("else:")
                compiler.indent_level += 1
                compiler._emit(f"_field_name = getattr({parent_var}, 'name', None)")
                compiler._emit(f"_field_def = {parent_var}")
                compiler.indent_level -= 1

                if field_name == "name":
                    compiler._emit(f'{result_var}["{alias}"] = _field_name')
                elif field_name == "description":
                    compiler._emit(f'{result_var}["{alias}"] = _field_def.description')
                elif field_name == "args":
                    compiler._emit("field_args = []")
                    compiler._emit("if _field_def.args:")
                    compiler.indent_level += 1
                    compiler._emit("for arg_name, arg_def in _field_def.args.items():")
                    compiler.indent_level += 1
                    compiler._emit("field_args.append((arg_name, arg_def))")
                    compiler.indent_level -= 1
                    compiler.indent_level -= 1

                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = []")
                        compiler._emit("for arg_tuple in field_args:")
                        compiler.indent_level += 1
                        compiler._emit("arg_result = {}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__InputValue",
                            "arg_tuple",
                            "arg_result",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler._emit(f"{result_var}['{alias}'].append(arg_result)")
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = field_args")
                elif field_name == "type":
                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = {{}}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__Type",
                            "_field_def.type",
                            f"{result_var}['{alias}']",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = _field_def.type")
                elif field_name == "isDeprecated":
                    compiler._emit(
                        f'{result_var}["{alias}"] = _field_def.deprecation_reason is not None'
                    )
                elif field_name == "deprecationReason":
                    compiler._emit(
                        f'{result_var}["{alias}"] = _field_def.deprecation_reason'
                    )

            elif introspection_type == "__InputValue":
                # __InputValue can be either a tuple (arg_name, arg_def) or just arg_def
                compiler._emit("# Handle __InputValue which may be a tuple")
                compiler._emit(f"if isinstance({parent_var}, tuple):")
                compiler.indent_level += 1
                compiler._emit(f"_input_name, _input_def = {parent_var}")
                compiler.indent_level -= 1
                compiler._emit("else:")
                compiler.indent_level += 1
                compiler._emit(f"_input_name = getattr({parent_var}, 'name', None)")
                compiler._emit(f"_input_def = {parent_var}")
                compiler.indent_level -= 1

                if field_name == "name":
                    compiler._emit(f'{result_var}["{alias}"] = _input_name')
                elif field_name == "description":
                    compiler._emit(
                        f'{result_var}["{alias}"] = _input_def.description if hasattr(_input_def, "description") else None'
                    )
                elif field_name == "type":
                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = {{}}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__Type",
                            "_input_def.type",
                            f"{result_var}['{alias}']",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                    else:
                        compiler._emit(
                            f"{result_var}['{alias}'] = _input_def.type if hasattr(_input_def, 'type') else None"
                        )
                elif field_name == "defaultValue":
                    compiler._emit("from graphql import Undefined")
                    compiler._emit(
                        "if hasattr(_input_def, 'default_value') and _input_def.default_value is not Undefined:"
                    )
                    compiler.indent_level += 1
                    compiler._emit(
                        f'{result_var}["{alias}"] = str(_input_def.default_value)'
                    )
                    compiler.indent_level -= 1
                    compiler._emit("else:")
                    compiler.indent_level += 1
                    compiler._emit(f'{result_var}["{alias}"] = None')
                    compiler.indent_level -= 1

            elif introspection_type == "__EnumValue":
                if field_name == "name":
                    compiler._emit(f'{result_var}["{alias}"] = {parent_var}.value')
                elif field_name == "description":
                    compiler._emit(
                        f'{result_var}["{alias}"] = {parent_var}.description'
                    )
                elif field_name == "isDeprecated":
                    compiler._emit(
                        f'{result_var}["{alias}"] = {parent_var}.deprecation_reason is not None'
                    )
                elif field_name == "deprecationReason":
                    compiler._emit(
                        f'{result_var}["{alias}"] = {parent_var}.deprecation_reason'
                    )

            elif introspection_type == "__Directive":
                if field_name == "name":
                    compiler._emit(f'{result_var}["{alias}"] = {parent_var}.name')
                elif field_name == "description":
                    compiler._emit(
                        f'{result_var}["{alias}"] = {parent_var}.description'
                    )
                elif field_name == "locations":
                    compiler._emit(
                        f'{result_var}["{alias}"] = [loc.name if hasattr(loc, "name") else str(loc) for loc in {parent_var}.locations]'
                    )
                elif field_name == "args":
                    compiler._emit("directive_args = []")
                    compiler._emit(f"if {parent_var}.args:")
                    compiler.indent_level += 1
                    compiler._emit(
                        f"for arg_name, arg_def in {parent_var}.args.items():"
                    )
                    compiler.indent_level += 1
                    compiler._emit("directive_args.append((arg_name, arg_def))")
                    compiler.indent_level -= 1
                    compiler.indent_level -= 1

                    if selection.selection_set:
                        compiler._emit(f"{result_var}['{alias}'] = []")
                        compiler._emit("for arg_tuple in directive_args:")
                        compiler.indent_level += 1
                        compiler._emit("arg_result = {}")
                        generate_introspection_selection(
                            compiler,
                            selection.selection_set,
                            "__InputValue",
                            "arg_tuple",
                            "arg_result",
                            info_var,
                            f"{path} + ['{alias}']",
                        )
                        compiler._emit(f"{result_var}['{alias}'].append(arg_result)")
                        compiler.indent_level -= 1
                    else:
                        compiler._emit(f"{result_var}['{alias}'] = directive_args")
