from __future__ import annotations

import inspect
import textwrap
from typing import Callable, Optional

from graphql import (
    DirectiveNode,
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLObjectType,
    GraphQLSchema,
    InlineFragmentNode,
    SelectionSetNode,
    Undefined,
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
        self.fragments = {}  # Maps fragment names to their definitions
        self.has_async_resolvers = False  # Track if any resolver is async
        self.async_resolver_ids = set()  # Track which resolvers are async

    def compile_query(self, query: str) -> Callable:
        document = parse(query)

        errors = validate(self.schema, document)
        if errors:
            raise ValueError(f"Query validation failed: {errors}")

        # Extract fragments from document
        self._extract_fragments(document)

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
        self.has_async_resolvers = False
        self.async_resolver_ids = set()

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

    def _extract_fragments(self, document: DocumentNode):
        """Extract fragment definitions from the document."""
        self.fragments = {}
        for definition in document.definitions:
            if isinstance(definition, FragmentDefinitionNode):
                self.fragments[definition.name.value] = definition

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

        # Pre-scan to detect async resolvers
        if operation.selection_set:
            self._detect_async_resolvers(operation.selection_set, root_type)

        # Add imports if needed
        if self.has_async_resolvers:
            self.generated_code.append("")
            self.generated_code.append("import asyncio")
            self.generated_code.append("import inspect")

        self.generated_code.append("")

        # Generate async or sync function based on resolver types
        if self.has_async_resolvers:
            self._emit("async def execute_query(root, context=None, variables=None):")
        else:
            self._emit("def execute_query(root, context=None, variables=None):")

        self.indent_level += 1
        self._emit('"""Execute the JIT-compiled GraphQL query."""')
        self._emit("result = {}")
        self._emit("errors = []  # Collect field errors")
        self._emit("info = _MockInfo(None)  # Mock info object")
        self._emit("info.root_value = root")
        self._emit("info.context = context")
        self._emit("info.variable_values = variables or {}")

        if operation.selection_set:
            # Generate try-except for root-level error handling
            self._emit("")
            self._emit("# Execute query with error handling")
            self._emit("try:")
            self.indent_level += 1
            self._generate_selection_set(
                operation.selection_set, root_type, "root", "result", "info", path="[]"
            )
            self.indent_level -= 1
            self._emit("except Exception as root_error:")
            self.indent_level += 1
            self._emit("# Non-nullable error propagated to root")
            self._emit("if not isinstance(root_error, Exception):")
            self.indent_level += 1
            self._emit("raise  # Re-raise non-Exception errors")
            self.indent_level -= 1
            self._emit("# Add to errors if it's a field error")
            self._emit("if not any(e.get('message') == str(root_error) for e in errors):")
            self.indent_level += 1
            self._emit("errors.append({'message': str(root_error), 'path': []})")
            self.indent_level -= 1
            self._emit("result = None  # Null the entire result for root error")
            self.indent_level -= 1

        self._emit("# Return result with errors if any occurred")
        self._emit("if errors:")
        self.indent_level += 1
        self._emit('return {"data": result, "errors": errors}')
        self.indent_level -= 1
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
        path: str = "[]",
    ):
        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                self._generate_field(
                    selection, parent_type, parent_var, result_var, info_var, path
                )
            elif isinstance(selection, FragmentSpreadNode):
                self._generate_fragment_spread(
                    selection, parent_type, parent_var, result_var, info_var
                )
            elif isinstance(selection, InlineFragmentNode):
                self._generate_inline_fragment(
                    selection, parent_type, parent_var, result_var, info_var
                )

    def _generate_field(
        self,
        field: FieldNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str = "[]",
    ):
        field_name = field.name.value
        alias = field.alias.value if field.alias else field_name
        
        # Build the path for this field
        field_path = f"{path} + ['{alias}']"

        if field_name == "__typename":
            self._emit(f'{result_var}["{alias}"] = "{parent_type.name}"')
            return

        field_def = parent_type.fields.get(field_name)
        if not field_def:
            return

        # Handle directives (@skip and @include)
        if field.directives:
            skip_code = self._generate_skip_include_checks(field.directives, info_var)
            if skip_code:
                self._emit(skip_code)
                self.indent_level += 1

        # Store the resolver for this field
        resolver_id = f"resolver_{self.field_counter}"
        self.field_counter += 1

        # Get the resolver function from the field definition
        if field_def.resolve:
            self.resolver_map[resolver_id] = field_def.resolve
            # Check if resolver is async
            if inspect.iscoroutinefunction(field_def.resolve):
                self.has_async_resolvers = True
                self.async_resolver_ids.add(resolver_id)
        else:
            # Use a default resolver that gets the attribute
            self.resolver_map[resolver_id] = None

        # Generate code to call the resolver
        temp_var = f"field_{field_name}_value"
        
        # Check if field is nullable for error handling
        is_nullable = self._is_nullable_type(field_def.type)

        # Update info object for this field
        self._emit(f'{info_var}.field_name = "{field_name}"')
        self._emit(f'{info_var}.parent_type = "{parent_type.name}"')
        
        # Start try block for error handling
        self._emit("try:")
        self.indent_level += 1

        # Handle field arguments if any
        if field.arguments or (field_def.args and len(field_def.args) > 0):
            # Build arguments dictionary including defaults
            self._emit("kwargs = {}")

            # First, handle default values from schema
            if field_def.args:
                for arg_name, arg_def in field_def.args.items():
                    if hasattr(arg_def, "default_value"):
                        # Skip Undefined sentinel values
                        if arg_def.default_value is not Undefined:
                            default_val = self._serialize_value(arg_def.default_value)
                            self._emit(f"kwargs['{arg_name}'] = {default_val}")

            # Then override with provided arguments
            if field.arguments:
                for arg in field.arguments:
                    arg_name = arg.name.value
                    arg_code = self._generate_argument_value(arg.value, info_var)
                    self._emit(f"kwargs['{arg_name}'] = {arg_code}")

        if self.resolver_map[resolver_id]:
            # Call the actual resolver
            self._emit(f"resolver = _resolvers['{resolver_id}']")
            if resolver_id in self.async_resolver_ids:
                # Async resolver - need to await
                if field.arguments or (field_def.args and len(field_def.args) > 0):
                    self._emit(
                        f"{temp_var} = await resolver({parent_var}, {info_var}, **kwargs)"
                    )
                else:
                    self._emit(f"{temp_var} = await resolver({parent_var}, {info_var})")
            # Sync resolver
            elif field.arguments or (field_def.args and len(field_def.args) > 0):
                self._emit(
                    f"{temp_var} = resolver({parent_var}, {info_var}, **kwargs)"
                )
            else:
                self._emit(f"{temp_var} = resolver({parent_var}, {info_var})")
        # Use default field resolution - arguments are passed to the method/function if it exists
        elif field.arguments or (field_def.args and len(field_def.args) > 0):
            self._emit(f"attr = getattr({parent_var}, '{field_name}', None)")
            self._emit("if callable(attr):")
            self.indent_level += 1
            if self.has_async_resolvers:
                # In async context, check if the method is async
                self._emit("if inspect.iscoroutinefunction(attr):")
                self.indent_level += 1
                self._emit(f"{temp_var} = await attr(**kwargs)")
                self.indent_level -= 1
                self._emit("else:")
                self.indent_level += 1
                self._emit(f"{temp_var} = attr(**kwargs)")
                self.indent_level -= 1
            else:
                self._emit(f"{temp_var} = attr(**kwargs)")
            self.indent_level -= 1
            self._emit("else:")
            self.indent_level += 1
            self._emit(f"{temp_var} = attr")
            self.indent_level -= 1
        # For simple attribute access without args
        elif self.has_async_resolvers:
            # Check if attribute is an async method
            self._emit(
                f"attr = getattr({parent_var}, '{field_name}', None) if hasattr({parent_var}, '{field_name}') else ({parent_var}.get('{field_name}', None) if isinstance({parent_var}, dict) else None)"
            )
            self._emit("if callable(attr) and inspect.iscoroutinefunction(attr):")
            self.indent_level += 1
            self._emit(f"{temp_var} = await attr()")
            self.indent_level -= 1
            self._emit("elif callable(attr):")
            self.indent_level += 1
            self._emit(f"{temp_var} = attr()")
            self.indent_level -= 1
            self._emit("else:")
            self.indent_level += 1
            self._emit(f"{temp_var} = attr")
            self.indent_level -= 1
        else:
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
                    self._emit(f"for idx_{field_name}, item_{field_name} in enumerate({temp_var}):")
                    self.indent_level += 1
                    self._emit(f"item_{field_name}_result = {{}}")
                    item_path = f"{field_path} + [idx_{field_name}]"
                    # Wrap nested selection in try-except for non-nullable propagation
                    self._emit("try:")
                    self.indent_level += 1
                    self._generate_selection_set(
                        field.selection_set,
                        field_type,
                        f"item_{field_name}",
                        f"item_{field_name}_result",
                        info_var,
                        item_path,
                    )
                    self._emit(
                        f'{result_var}["{alias}"].append(item_{field_name}_result)'
                    )
                    self.indent_level -= 1
                    self._emit("except Exception as nested_e:")
                    self.indent_level += 1
                    self._emit("# Error in list item - check if list is nullable")
                    if is_nullable:
                        self._emit("# List is nullable, null the item")
                        self._emit(f'{result_var}["{alias}"].append(None)')
                    else:
                        self._emit("# List is non-nullable, propagate error")
                        self._emit("raise")
                    self.indent_level -= 1
                    self.indent_level -= 1
                    self.indent_level -= 1
                    self._emit("else:")
                    self.indent_level += 1
                    self._emit("single_item_result = {}")
                    # Wrap single item in try-except
                    self._emit("try:")
                    self.indent_level += 1
                    self._generate_selection_set(
                        field.selection_set,
                        field_type,
                        temp_var,
                        "single_item_result",
                        info_var,
                        field_path,
                    )
                    self._emit(f'{result_var}["{alias}"] = single_item_result')
                    self.indent_level -= 1
                    self._emit("except Exception as nested_e:")
                    self.indent_level += 1
                    if is_nullable:
                        self._emit("# Field is nullable, set to None")
                        self._emit(f'{result_var}["{alias}"] = None')
                    else:
                        self._emit("# Field is non-nullable, propagate error")
                        self._emit("raise")
                    self.indent_level -= 1
                    self.indent_level -= 1
                else:
                    nested_var = f"nested_{field_name}_result"
                    self._emit(f"{nested_var} = {{}}")
                    # Wrap nested selection in try-except
                    self._emit("try:")
                    self.indent_level += 1
                    self._generate_selection_set(
                        field.selection_set, field_type, temp_var, nested_var, info_var, field_path
                    )
                    self._emit(f'{result_var}["{alias}"] = {nested_var}')
                    self.indent_level -= 1
                    self._emit("except Exception as nested_e:")
                    self.indent_level += 1
                    if is_nullable:
                        self._emit("# Field is nullable, set to None")
                        self._emit(f'{result_var}["{alias}"] = None')
                    else:
                        self._emit("# Field is non-nullable, propagate error")
                        self._emit("raise")
                    self.indent_level -= 1

                self.indent_level -= 1
                self._emit("else:")
                self.indent_level += 1
                self._emit(f'{result_var}["{alias}"] = None')
                self.indent_level -= 1
        else:
            self._emit(f'{result_var}["{alias}"] = {temp_var}')
        
        # End try block and add except for error handling
        self.indent_level -= 1
        self._emit("except Exception as e:")
        self.indent_level += 1
        self._emit(f"# Handle field error for '{field_name}'")
        self._emit(f"error = {{}}")
        self._emit(f"error['message'] = str(e)")
        self._emit(f"error['path'] = {field_path}")
        self._emit("errors.append(error)")
        
        if is_nullable:
            self._emit(f"# Nullable field - set to None")
            self._emit(f'{result_var}["{alias}"] = None')
        else:
            self._emit(f"# Non-nullable field error - must propagate")
            self._emit("# Re-raise to propagate error up the tree")
            self._emit("raise")
        self.indent_level -= 1

        # Close directive conditional block if needed
        if field.directives and self._generate_skip_include_checks(
            field.directives, info_var
        ):
            self.indent_level -= 1

    def _generate_argument_value(self, value_node, info_var: str) -> str:
        """Generate code to extract argument value from AST node, supporting variables"""
        from graphql.language import (
            BooleanValueNode,
            EnumValueNode,
            FloatValueNode,
            IntValueNode,
            ListValueNode,
            NullValueNode,
            ObjectValueNode,
            StringValueNode,
            VariableNode,
        )

        if isinstance(value_node, VariableNode):
            # Reference to a variable
            var_name = value_node.name.value
            return f"{info_var}.variable_values.get('{var_name}')"
        if isinstance(value_node, (IntValueNode, FloatValueNode)):
            return value_node.value
        if isinstance(value_node, StringValueNode):
            return repr(value_node.value)
        if isinstance(value_node, BooleanValueNode):
            return "True" if value_node.value else "False"
        if isinstance(value_node, NullValueNode):
            return "None"
        if isinstance(value_node, EnumValueNode):
            return repr(value_node.value)
        if isinstance(value_node, ListValueNode):
            items = [
                self._generate_argument_value(item, info_var)
                for item in value_node.values
            ]
            return f"[{', '.join(items)}]"
        if isinstance(value_node, ObjectValueNode):
            items = []
            for field in value_node.fields:
                key = repr(field.name.value)
                val = self._generate_argument_value(field.value, info_var)
                items.append(f"{key}: {val}")
            return f"{{{', '.join(items)}}}"
        # Fallback for unknown types
        if hasattr(value_node, "value"):
            return repr(value_node.value)
        return "None"

    def _serialize_value(self, value) -> str:
        """Serialize a Python value to a string representation for code generation"""
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return repr(value)
        if isinstance(value, list):
            items = [self._serialize_value(item) for item in value]
            return f"[{', '.join(items)}]"
        if isinstance(value, dict):
            items = [f"{k!r}: {self._serialize_value(v)}" for k, v in value.items()]
            return f"{{{', '.join(items)}}}"
        return repr(value)

    def _generate_fragment_spread(
        self,
        fragment_spread: FragmentSpreadNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
    ):
        """Generate code for a fragment spread."""
        fragment_name = fragment_spread.name.value

        if fragment_name not in self.fragments:
            raise ValueError(f"Fragment '{fragment_name}' not found")

        fragment_def = self.fragments[fragment_name]

        # Get the type condition
        type_condition = fragment_def.type_condition.name.value

        # Check if the parent type matches or is compatible with the fragment's type condition
        if parent_type.name == type_condition:
            # The types match, we can directly apply the fragment
            if fragment_def.selection_set:
                self._generate_selection_set(
                    fragment_def.selection_set,
                    parent_type,
                    parent_var,
                    result_var,
                    info_var,
                )
        else:
            # Generate a type check for the fragment
            self._emit(f"# Fragment spread: {fragment_name}")
            self._emit(
                f"if hasattr({parent_var}, '__typename') and {parent_var}.__typename == '{type_condition}':"
            )
            self.indent_level += 1
            if fragment_def.selection_set:
                self._generate_selection_set(
                    fragment_def.selection_set,
                    parent_type,
                    parent_var,
                    result_var,
                    info_var,
                )
            self.indent_level -= 1

    def _generate_inline_fragment(
        self,
        inline_fragment: InlineFragmentNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
    ):
        """Generate code for an inline fragment."""
        # Check if there's a type condition
        if inline_fragment.type_condition:
            type_name = inline_fragment.type_condition.name.value

            # Get the actual type from schema
            fragment_type = self.schema.type_map.get(type_name)
            if not fragment_type or not isinstance(fragment_type, GraphQLObjectType):
                return  # Skip if type not found

            # If the type condition matches the parent type, apply directly
            if type_name == parent_type.name:
                # Same type, no need for runtime check
                self._emit(f"# Inline fragment on {type_name}")
                if inline_fragment.selection_set:
                    self._generate_selection_set(
                        inline_fragment.selection_set,
                        fragment_type,
                        parent_var,
                        result_var,
                        info_var,
                    )
            else:
                # Different type, need runtime check
                self._emit(f"# Inline fragment on {type_name}")
                self._emit(
                    f"if hasattr({parent_var}, '__typename') and {parent_var}.__typename == '{type_name}':"
                )
                self.indent_level += 1

                if inline_fragment.selection_set:
                    self._generate_selection_set(
                        inline_fragment.selection_set,
                        fragment_type,
                        parent_var,
                        result_var,
                        info_var,
                    )

                self.indent_level -= 1
        # No type condition, apply selections directly
        elif inline_fragment.selection_set:
            self._generate_selection_set(
                inline_fragment.selection_set,
                parent_type,
                parent_var,
                result_var,
                info_var,
            )

    def _generate_skip_include_checks(
        self, directives: list[DirectiveNode], info_var: str
    ) -> str:
        """Generate conditional code for @skip and @include directives."""
        conditions = []

        for directive in directives:
            directive_name = directive.name.value

            if directive_name == "skip":
                # @skip(if: condition) - skip field if condition is true
                if_arg = self._get_directive_argument(directive, "if", info_var)
                if if_arg:
                    conditions.append(f"not ({if_arg})")
            elif directive_name == "include":
                # @include(if: condition) - include field if condition is true
                if_arg = self._get_directive_argument(directive, "if", info_var)
                if if_arg:
                    conditions.append(if_arg)

        if conditions:
            # Combine all conditions with AND
            return f"if {' and '.join(conditions)}:"
        return ""

    def _get_directive_argument(
        self, directive: DirectiveNode, arg_name: str, info_var: str
    ) -> str:
        """Extract argument value from a directive."""
        for arg in directive.arguments or []:
            if arg.name.value == arg_name:
                return self._generate_argument_value(arg.value, info_var)
        return ""

    def _detect_async_resolvers(
        self, selection_set: SelectionSetNode, parent_type: GraphQLObjectType
    ):
        """Pre-scan to detect any async resolvers in the query."""
        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                if field_name == "__typename":
                    continue

                field_def = parent_type.fields.get(field_name)
                if field_def:
                    if field_def.resolve and inspect.iscoroutinefunction(
                        field_def.resolve
                    ):
                        self.has_async_resolvers = True
                    # Also check if the default field access might be async
                    # This is a heuristic - in production we'd need schema introspection
                    elif not field_def.resolve:
                        # For fields without custom resolvers, we can't know at compile time
                        # if the attribute/method is async, so we need to be conservative
                        # For now, we'll assume fields ending with certain patterns might be async
                        pass

                # Recurse into nested selections
                if field_def and selection.selection_set:
                    field_type = field_def.type
                    while hasattr(field_type, "of_type"):
                        field_type = field_type.of_type
                    if isinstance(field_type, GraphQLObjectType):
                        self._detect_async_resolvers(
                            selection.selection_set, field_type
                        )
            elif isinstance(selection, FragmentSpreadNode):
                # Handle fragment spreads
                fragment_name = selection.name.value
                if fragment_name in self.fragments:
                    fragment_def = self.fragments[fragment_name]
                    if fragment_def.selection_set:
                        self._detect_async_resolvers(
                            fragment_def.selection_set, parent_type
                        )
            elif isinstance(selection, InlineFragmentNode):
                # Handle inline fragments
                if selection.selection_set:
                    if selection.type_condition:
                        type_name = selection.type_condition.name.value
                        fragment_type = self.schema.type_map.get(type_name)
                        if fragment_type and isinstance(
                            fragment_type, GraphQLObjectType
                        ):
                            self._detect_async_resolvers(
                                selection.selection_set, fragment_type
                            )
                    else:
                        self._detect_async_resolvers(
                            selection.selection_set, parent_type
                        )

    def _emit(self, line: str):
        indent = "    " * self.indent_level
        self.generated_code.append(f"{indent}{line}")
    
    def _is_nullable_type(self, graphql_type):
        """Check if a GraphQL type is nullable."""
        from graphql import GraphQLNonNull
        return not isinstance(graphql_type, GraphQLNonNull)


def compile_query(schema: GraphQLSchema, query: str) -> Callable:
    compiler = GraphQLJITCompiler(schema)
    return compiler.compile_query(query)
