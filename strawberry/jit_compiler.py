from __future__ import annotations

import textwrap
from typing import Callable, Optional

from graphql import (
    DocumentNode,
    FieldNode,
    GraphQLObjectType,
    GraphQLSchema,
    SelectionSetNode,
    get_operation_root_type,
    parse,
    validate,
)
from graphql.language import OperationDefinitionNode


class MockInfo:
    """Mock GraphQLResolveInfo for JIT compilation"""

    def __init__(self, schema: GraphQLSchema):
        self.schema = schema
        self.field_name = None
        self.parent_type = None
        self.return_type = None
        self.path = []
        self.operation = None
        self.variable_values = {}
        self.context = None
        self.root_value = None
        self.fragments = {}


class GraphQLJITCompiler:
    def __init__(self, schema: GraphQLSchema):
        self.schema = schema
        self.generated_code = []
        self.indent_level = 0
        self.field_counter = 0
        self.resolver_map = {}  # Maps field IDs to their resolvers

    def compile_query(self, query: str) -> Callable:
        document = parse(query)

        errors = validate(self.schema, document)
        if errors:
            raise ValueError(f"Query validation failed: {errors}")

        operation = self._get_operation(document)
        if not operation:
            raise ValueError("No operation found in query")

        root_type = get_operation_root_type(self.schema, operation)
        if not root_type:
            raise ValueError("Could not determine root type")

        # Reset state for new compilation
        self.generated_code = []
        self.indent_level = 0
        self.field_counter = 0
        self.resolver_map = {}

        function_code = self._generate_function(operation, root_type)

        # For runtime execution, we need to provide the actual resolvers
        # Remove the resolver initialization lines and the empty _resolvers declaration
        lines = function_code.split("\n")
        filtered_lines = []
        skip_resolver_init = False
        for line in lines:
            # Skip the empty resolver map initialization
            if line.strip() == "_resolvers = {}":
                continue
            # Skip resolver initialization section
            if line.strip().startswith(
                "# Initialize resolvers for standalone execution"
            ):
                skip_resolver_init = True
            elif skip_resolver_init and (
                not line.strip()
                or line.strip().startswith("if __name__ == '__main__':")
            ):
                skip_resolver_init = False
                if line.strip().startswith("if __name__ == '__main__':"):
                    filtered_lines.append(line)
            elif not skip_resolver_init:
                filtered_lines.append(line)

        runtime_code = "\n".join(filtered_lines)

        # Create the resolver map as a local variable in the compiled function
        local_vars = {
            "_resolvers": self.resolver_map,
            "_MockInfo": MockInfo,
        }

        compiled_code = compile(runtime_code, "<generated>", "exec")
        exec(compiled_code, local_vars)

        return local_vars["execute_query"]

    def _get_operation(
        self, document: DocumentNode
    ) -> Optional[OperationDefinitionNode]:
        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                return definition
        return None

    def _generate_function(
        self, operation: OperationDefinitionNode, root_type: GraphQLObjectType
    ) -> str:
        self.generated_code = []
        self.indent_level = 0

        # Extract operation details for documentation
        operation_name = operation.name.value if operation.name else "anonymous"
        operation_type = operation.operation.value

        # Get field selections for documentation
        fields_selected = []
        if operation.selection_set:
            for selection in operation.selection_set.selections:
                if hasattr(selection, "name"):
                    fields_selected.append(selection.name.value)

        # Add standalone header with imports and MockInfo class
        header_template = '''#!/usr/bin/env python
"""
Standalone JIT-compiled GraphQL executor.
This file was automatically generated and can be executed independently.

Query Details:
- Operation: {operation_type} {operation_name}
- Root Type: {root_type_name}
- Top-level Fields: {fields}
- Generated: {generated_time}
"""

from typing import Any, Dict, List, Optional'''

        header = header_template.format(
            operation_type=operation_type,
            operation_name=operation_name,
            root_type_name=root_type.name,
            fields=", ".join(fields_selected) if fields_selected else "none",
            generated_time="[timestamp]",  # Use placeholder for deterministic snapshots
        )

        # Add the MockInfo class and resolver setup
        mock_info_code = textwrap.dedent("""

        class _MockInfo:
            \"\"\"Mock GraphQLResolveInfo for JIT execution.\"\"\"
            def __init__(self, schema):
                self.schema = schema
                self.field_name = None
                self.parent_type = None
                self.return_type = None
                self.path = []
                self.operation = None
                self.variable_values = {}
                self.context = None
                self.root_value = None
                self.fragments = {}


        def _default_resolver(obj, info):
            \"\"\"Default field resolver that gets attributes or dict values.\"\"\"
            field_name = info.field_name
            if hasattr(obj, field_name):
                return getattr(obj, field_name)
            elif isinstance(obj, dict):
                return obj.get(field_name)
            return None


        # Resolver map - will be populated with actual resolvers at runtime
        # For standalone execution, these will use the default resolver
        _resolvers = {}
        """).strip()

        self.generated_code.append(header)
        self.generated_code.append(mock_info_code)
        self.generated_code.append("")
        self.generated_code.append("")

        self._emit("def execute_query(root, context=None, variables=None):")
        self.indent_level += 1
        self._emit('"""Execute the JIT-compiled GraphQL query."""')
        self._emit("result = {}")
        self._emit("info = _MockInfo(None)  # Mock info object")
        self._emit("info.root_value = root")
        self._emit("info.context = context")
        self._emit("info.variable_values = variables or {}")

        if operation.selection_set:
            self._generate_selection_set(
                operation.selection_set, root_type, "root", "result", "info"
            )

        self._emit("return result")

        # Generate resolver initialization
        self.indent_level = 0
        self.generated_code.append("")
        self.generated_code.append("")
        self._emit("# Initialize resolvers for standalone execution")
        for resolver_id in self.resolver_map:
            if self.resolver_map[resolver_id] is None:
                self._emit(f"_resolvers['{resolver_id}'] = _default_resolver")
            else:
                # For custom resolvers, we'll use default resolver in standalone mode
                # since we can't serialize the actual function
                self._emit(
                    f"_resolvers['{resolver_id}'] = _default_resolver  # Custom resolver in actual execution"
                )

        # Add main block for standalone execution
        self.generated_code.append("")
        self.generated_code.append("")
        self._emit("if __name__ == '__main__':")
        self.indent_level += 1
        self._emit("# Example usage when run standalone")
        self._emit("print('This is a JIT-compiled GraphQL executor.')")
        self._emit(
            "print('To use it, import and call execute_query() with your root object.')"
        )
        self._emit("print()")
        self._emit("print('Example:')")
        self._emit("print('  from this_file import execute_query')")
        self._emit("print('  result = execute_query(root_object)')")
        self._emit("print('  print(result)')")
        self._emit("")
        self._emit("# Demo with sample data")
        self._emit("class SampleObject:")
        self.indent_level += 1
        self._emit("def __init__(self, **kwargs):")
        self.indent_level += 1
        self._emit("for k, v in kwargs.items():")
        self.indent_level += 1
        self._emit("setattr(self, k, v)")
        self.indent_level -= 3
        self._emit("")
        self._emit("# You can test with your own data structure here")
        self._emit("# sample_root = SampleObject(...)")
        self._emit("# result = execute_query(sample_root)")
        self._emit("# print(result)")

        code = "\n".join(self.generated_code)
        return code

    def _generate_selection_set(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
    ):
        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                self._generate_field(
                    selection, parent_type, parent_var, result_var, info_var
                )

    def _generate_field(
        self,
        field: FieldNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
    ):
        field_name = field.name.value
        alias = field.alias.value if field.alias else field_name

        if field_name == "__typename":
            self._emit(f'{result_var}["{alias}"] = "{parent_type.name}"')
            return

        field_def = parent_type.fields.get(field_name)
        if not field_def:
            return

        # Store the resolver for this field
        resolver_id = f"resolver_{self.field_counter}"
        self.field_counter += 1

        # Get the resolver function from the field definition
        if field_def.resolve:
            self.resolver_map[resolver_id] = field_def.resolve
        else:
            # Use a default resolver that gets the attribute
            self.resolver_map[resolver_id] = None

        # Generate code to call the resolver
        temp_var = f"field_{field_name}_value"

        # Update info object for this field
        self._emit(f'{info_var}.field_name = "{field_name}"')
        self._emit(f'{info_var}.parent_type = "{parent_type.name}"')

        if self.resolver_map[resolver_id]:
            # Call the actual resolver
            self._emit(f"resolver = _resolvers['{resolver_id}']")
            # Handle field arguments if any
            if field.arguments:
                args_dict = self._build_arguments_dict(field)
                self._emit(f"kwargs = {args_dict}")
                self._emit(f"{temp_var} = resolver({parent_var}, {info_var}, **kwargs)")
            else:
                self._emit(f"{temp_var} = resolver({parent_var}, {info_var})")
        else:
            # Use default field resolution
            self._emit(
                f"{temp_var} = getattr({parent_var}, '{field_name}', None) if hasattr({parent_var}, '{field_name}') else ({parent_var}.get('{field_name}', None) if isinstance({parent_var}, dict) else None)"
            )

        if field.selection_set:
            field_type = field_def.type
            while hasattr(field_type, "of_type"):
                field_type = field_type.of_type

            if isinstance(field_type, GraphQLObjectType):
                self._emit(f"if {temp_var} is not None:")
                self.indent_level += 1

                # Check if it's a list type
                if hasattr(field_def.type, "of_type") and str(
                    field_def.type
                ).startswith("["):
                    self._emit(f"if isinstance({temp_var}, list):")
                    self.indent_level += 1
                    self._emit(f'{result_var}["{alias}"] = []')
                    self._emit(f"for item_{field_name} in {temp_var}:")
                    self.indent_level += 1
                    self._emit(f"item_{field_name}_result = {{}}")
                    self._generate_selection_set(
                        field.selection_set,
                        field_type,
                        f"item_{field_name}",
                        f"item_{field_name}_result",
                        info_var,
                    )
                    self._emit(
                        f'{result_var}["{alias}"].append(item_{field_name}_result)'
                    )
                    self.indent_level -= 1
                    self.indent_level -= 1
                    self._emit("else:")
                    self.indent_level += 1
                    self._emit("single_item_result = {}")
                    self._generate_selection_set(
                        field.selection_set,
                        field_type,
                        temp_var,
                        "single_item_result",
                        info_var,
                    )
                    self._emit(f'{result_var}["{alias}"] = single_item_result')
                    self.indent_level -= 1
                else:
                    nested_var = f"nested_{field_name}_result"
                    self._emit(f"{nested_var} = {{}}")
                    self._generate_selection_set(
                        field.selection_set, field_type, temp_var, nested_var, info_var
                    )
                    self._emit(f'{result_var}["{alias}"] = {nested_var}')

                self.indent_level -= 1
                self._emit("else:")
                self.indent_level += 1
                self._emit(f'{result_var}["{alias}"] = None')
                self.indent_level -= 1
        else:
            self._emit(f'{result_var}["{alias}"] = {temp_var}')

    def _build_arguments_dict(self, field: FieldNode) -> str:
        """Build a dictionary of arguments from the field node"""
        args = {}
        for arg in field.arguments:
            # For now, just handle simple literal values
            arg_name = arg.name.value
            if hasattr(arg.value, "value"):
                args[arg_name] = arg.value.value
        return str(args)

    def _emit(self, line: str):
        indent = "    " * self.indent_level
        self.generated_code.append(f"{indent}{line}")


def compile_query(schema: GraphQLSchema, query: str) -> Callable:
    compiler = GraphQLJITCompiler(schema)
    return compiler.compile_query(query)
