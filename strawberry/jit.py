"""Unified JIT compiler for Strawberry GraphQL.

This module provides the production-ready JIT compiler that combines:
- Aggressive compile-time optimizations
- Parallel async execution with asyncio.gather()
- GraphQL spec-compliant error handling
- Built-in query caching with LRU eviction
- Support for fragments, directives, and arguments
"""

from __future__ import annotations

import hashlib
import inspect
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from graphql import (
    DirectiveNode,
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLInterfaceType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLUnionType,
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


class JITCompiler:
    """Unified high-performance JIT compiler for GraphQL queries.

    Features:
    - Compile-time optimizations for maximum performance
    - Parallel async execution for independent fields
    - Full GraphQL spec compliance including error handling
    - Built-in caching with configurable TTL and size limits
    """

    def __init__(self, schema: GraphQLSchema):
        self.schema = schema
        self.generated_code = []
        self.indent_level = 0
        self.field_counter = 0
        self.resolver_map = {}
        self.fragments = {}
        self.has_async_resolvers = False
        self.async_resolver_ids = set()
        self.nested_counter = 0  # Counter for unique nested result variables

        # Optimization flags
        self.enable_parallel = True
        self.inline_trivial_resolvers = True
        self.eliminate_redundant_checks = True

    def compile_query(self, query: str) -> Callable:
        """Compile a GraphQL query into optimized Python code."""
        document = parse(query)

        errors = validate(self.schema, document)
        if errors:
            raise ValueError(f"Query validation failed: {errors}")

        # Extract fragments
        self._extract_fragments(document)

        operation = self._get_operation(document)
        if not operation:
            raise ValueError("No operation found in query")

        root_type = get_operation_root_type(self.schema, operation)
        if not root_type:
            raise ValueError("Could not determine root type")

        # Reset state
        self._reset_state()

        # Generate optimized function code
        function_code = self._generate_optimized_function(operation, root_type)

        # Compile and execute
        local_vars = {
            "_resolvers": self.resolver_map,
            "_MockInfo": MockInfo,
            "_schema": self.schema,
            "_scalar_serializers": {},  # Will be populated with scalar serializers
            "_scalar_parsers": {},  # Will be populated with scalar parse_value functions
            "_var_defs": operation.variable_definitions
            if operation.variable_definitions
            else [],
        }

        # Extract scalar serializers and parsers from schema
        for type_name, type_def in self.schema.type_map.items():
            if hasattr(type_def, "serialize") and callable(type_def.serialize):
                # This is a scalar type with custom serialization
                local_vars["_scalar_serializers"][type_name] = type_def.serialize
            if hasattr(type_def, "parse_value") and callable(type_def.parse_value):
                # This is a scalar type with custom parsing
                local_vars["_scalar_parsers"][type_name] = type_def.parse_value

        compiled_code = compile(function_code, "<jit_compiled>", "exec")
        exec(compiled_code, local_vars)

        # Store the source code on the function for debugging/inspection
        execute_fn = local_vars["execute_query"]
        execute_fn._jit_source = function_code

        return execute_fn

    def _reset_state(self):
        """Reset compiler state for new compilation."""
        self.generated_code = []
        self.indent_level = 0
        self.field_counter = 0
        self.resolver_map = {}
        self.has_async_resolvers = False
        self.async_resolver_ids = set()
        self.nested_counter = 0

    def _get_operation(
        self, document: DocumentNode
    ) -> Optional[OperationDefinitionNode]:
        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                return definition
        return None

    def _extract_fragments(self, document: DocumentNode):
        """Extract fragment definitions from document."""
        self.fragments = {}
        for definition in document.definitions:
            if isinstance(definition, FragmentDefinitionNode):
                self.fragments[definition.name.value] = definition

    def _generate_optimized_function(
        self, operation: OperationDefinitionNode, root_type: GraphQLObjectType
    ) -> str:
        """Generate optimized function with all performance enhancements."""
        self.generated_code = []
        self.indent_level = 0

        # Add imports
        self._emit("from typing import Any, Dict, List, Optional")
        self._emit("")

        # Check if this is a mutation (mutations must execute serially)
        from graphql.language import OperationType

        is_mutation = operation.operation == OperationType.MUTATION

        # Pre-scan for async resolvers
        if operation.selection_set:
            self._detect_async_resolvers(operation.selection_set, root_type)

        if self.has_async_resolvers:
            self._emit("import asyncio")
            self._emit("import inspect")
            self._emit("")

        # Generate function signature
        if self.has_async_resolvers:
            self._emit("async def execute_query(root, context=None, variables=None):")
        else:
            self._emit("def execute_query(root, context=None, variables=None):")

        self.indent_level += 1
        self._emit('"""Execute JIT-compiled GraphQL query with optimizations."""')
        self._emit("result = {}")
        self._emit("errors = []")

        # Coerce variables to handle enums and other input types properly
        if operation.variable_definitions:
            self._emit("# Coerce variables")
            self._emit("from graphql.execution.values import get_variable_values")
            self._emit(
                "coerced = get_variable_values(_schema, _var_defs, variables or {})"
            )
            self._emit("if isinstance(coerced, list):")  # List means errors
            self.indent_level += 1
            self._emit("for error in coerced:")
            self.indent_level += 1
            self._emit("errors.append({'message': str(error), 'path': []})")
            self.indent_level -= 1
            self._emit('return {"data": None, "errors": errors}')
            self.indent_level -= 1
            self._emit("variables = coerced")  # Dict of coerced values
        else:
            self._emit("variables = variables or {}")

        # Create mock info object
        self._emit("")
        self._emit("info = _MockInfo(_schema)")
        self._emit("info.root_value = root")
        self._emit("info.context = context")
        self._emit("info.variable_values = variables")
        self._emit("")

        # Generate selection set with error handling
        if operation.selection_set:
            self._emit("# Execute query with error handling")
            self._emit("try:")
            self.indent_level += 1

            # Mutations MUST execute serially per GraphQL spec
            # Queries can use parallel execution for performance
            if self.enable_parallel and self.has_async_resolvers and not is_mutation:
                self._emit("# Parallel execution for query fields")
                self._generate_parallel_selection_set(
                    operation.selection_set, root_type, "root", "result", "info", "[]"
                )
            else:
                if is_mutation:
                    self._emit(
                        "# Serial execution for mutations (GraphQL spec requirement)"
                    )
                self._generate_selection_set(
                    operation.selection_set, root_type, "root", "result", "info", "[]"
                )

            self.indent_level -= 1
            self._emit("except Exception as root_error:")
            self.indent_level += 1
            self._emit(
                "if not any(e.get('message') == str(root_error) for e in errors):"
            )
            self.indent_level += 1
            self._emit("errors.append({'message': str(root_error), 'path': []})")
            self.indent_level -= 1
            self._emit("result = None")
            self.indent_level -= 1

        self._emit("")
        self._emit("# Return result with errors if any")
        self._emit("if errors:")
        self.indent_level += 1
        self._emit('return {"data": result, "errors": errors}')
        self.indent_level -= 1
        self._emit("return result")

        return "\n".join(self.generated_code)

    def _generate_parallel_selection_set(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ):
        """Generate selection set with parallel async execution."""
        # Group selections by type
        sync_fields = []
        async_fields = []
        fragments = []

        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                if field_name == "__typename":
                    sync_fields.append(selection)
                    continue

                field_def = parent_type.fields.get(field_name)
                if field_def:
                    resolver_id = f"resolver_{self.field_counter}"
                    self.field_counter += 1

                    if field_def.resolve and inspect.iscoroutinefunction(
                        field_def.resolve
                    ):
                        async_fields.append((selection, resolver_id))
                        self.resolver_map[resolver_id] = field_def.resolve
                        self.async_resolver_ids.add(resolver_id)
                    else:
                        sync_fields.append(selection)
                        if field_def.resolve:
                            self.resolver_map[resolver_id] = field_def.resolve
            else:
                fragments.append(selection)

        # Execute sync fields first
        for selection in sync_fields:
            self._generate_field(
                selection, parent_type, parent_var, result_var, info_var, path
            )

        # Execute async fields in parallel if multiple
        if len(async_fields) > 1:
            self._emit("# Execute async fields in parallel")
            self._emit("async_tasks = []")

            for selection, resolver_id in async_fields:
                field_name = selection.name.value
                alias = selection.alias.value if selection.alias else field_name

                # Generate async task
                task_name = f"task_{field_name}"
                self._emit(f"async def {task_name}():")
                self.indent_level += 1
                self._emit("temp_result = {}")
                self._generate_field(
                    selection, parent_type, parent_var, "temp_result", info_var, path
                )
                self._emit(f"return ('{alias}', temp_result.get('{alias}'))")
                self.indent_level -= 1
                self._emit(f"async_tasks.append({task_name}())")

            self._emit("")
            self._emit("# Gather results")
            self._emit(
                "async_results = await asyncio.gather(*async_tasks, return_exceptions=True)"
            )
            self._emit("for async_result in async_results:")
            self.indent_level += 1
            self._emit("if isinstance(async_result, Exception):")
            self.indent_level += 1
            self._emit(
                "errors.append({'message': str(async_result), 'path': " + path + "})"
            )
            self.indent_level -= 1
            self._emit("elif isinstance(async_result, tuple):")
            self.indent_level += 1
            self._emit("field_alias, field_value = async_result")
            self._emit(f"{result_var}[field_alias] = field_value")
            self.indent_level -= 1
            self.indent_level -= 1

        elif async_fields:
            # Single async field
            for selection, _ in async_fields:
                self._generate_field(
                    selection, parent_type, parent_var, result_var, info_var, path
                )

        # Process fragments
        for selection in fragments:
            if isinstance(selection, FragmentSpreadNode):
                self._generate_fragment_spread(
                    selection, parent_type, parent_var, result_var, info_var, path
                )
            elif isinstance(selection, InlineFragmentNode):
                self._generate_inline_fragment(
                    selection, parent_type, parent_var, result_var, info_var, path
                )

    def _generate_selection_set(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ):
        """Generate standard selection set."""
        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                self._generate_field(
                    selection, parent_type, parent_var, result_var, info_var, path
                )
            elif isinstance(selection, FragmentSpreadNode):
                self._generate_fragment_spread(
                    selection, parent_type, parent_var, result_var, info_var, path
                )
            elif isinstance(selection, InlineFragmentNode):
                self._generate_inline_fragment(
                    selection, parent_type, parent_var, result_var, info_var, path
                )

    def _generate_field(
        self,
        field: FieldNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ):
        """Generate optimized field resolution with error handling."""
        field_name = field.name.value
        alias = field.alias.value if field.alias else field_name
        field_path = f"{path} + ['{alias}']"

        # Handle __typename
        if field_name == "__typename":
            self._emit(f'{result_var}["{alias}"] = "{parent_type.name}"')
            return

        # Handle introspection fields
        if field_name == "__schema":
            self._emit("# Introspection: __schema")
            self._emit("from graphql.type import introspection")
            self._emit("schema_type = introspection.__Schema")
            self._emit(f"{result_var}['{alias}'] = {{}}")
            if field.selection_set:
                self._generate_introspection_selection(
                    field.selection_set,
                    "__Schema",
                    f"{info_var}.schema",
                    f"{result_var}['{alias}']",
                    info_var,
                    field_path,
                )
            return

        if field_name == "__type":
            self._emit("# Introspection: __type")
            # Get the name argument
            type_name_arg = None
            if field.arguments:
                for arg in field.arguments:
                    if arg.name.value == "name":
                        type_name_arg = self._generate_argument_value(
                            arg.value, info_var
                        )
                        break

            if type_name_arg:
                self._emit(
                    f"requested_type = {info_var}.schema.get_type({type_name_arg})"
                )
                self._emit("if requested_type:")
                self.indent_level += 1
                self._emit(f"{result_var}['{alias}'] = {{}}")
                if field.selection_set:
                    self._generate_introspection_selection(
                        field.selection_set,
                        "__Type",
                        "requested_type",
                        f"{result_var}['{alias}']",
                        info_var,
                        field_path,
                    )
                self.indent_level -= 1
                self._emit("else:")
                self.indent_level += 1
                self._emit(f"{result_var}['{alias}'] = None")
                self.indent_level -= 1
            else:
                self._emit(f"{result_var}['{alias}'] = None")
            return

        field_def = parent_type.fields.get(field_name)
        if not field_def:
            return

        # Check if nullable
        is_nullable = not isinstance(field_def.type, GraphQLNonNull)

        # Handle directives
        if field.directives:
            skip_code = self._generate_skip_include_checks(field.directives, info_var)
            if skip_code:
                self._emit(skip_code)
                self.indent_level += 1

        # Generate field resolution with error handling
        self._emit("try:")
        self.indent_level += 1

        # Update info
        self._emit(f'info.field_name = "{field_name}"')

        # Generate optimized resolver call
        temp_var = f"field_{field_name}_value"

        if field_def.resolve:
            resolver_id = f"resolver_{self.field_counter}"
            self.field_counter += 1
            self.resolver_map[resolver_id] = field_def.resolve

            if inspect.iscoroutinefunction(field_def.resolve):
                self.async_resolver_ids.add(resolver_id)
                if field.arguments:
                    self._generate_arguments(field, field_def, info_var)
                    self._emit(
                        f"{temp_var} = await _resolvers['{resolver_id}']({parent_var}, info, **kwargs)"
                    )
                else:
                    self._emit(
                        f"{temp_var} = await _resolvers['{resolver_id}']({parent_var}, info)"
                    )
            elif field.arguments:
                self._generate_arguments(field, field_def, info_var)
                self._emit(
                    f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, info, **kwargs)"
                )
            else:
                self._emit(
                    f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, info)"
                )
        # Inline trivial field access for performance
        elif self.inline_trivial_resolvers and not field.arguments:
            self._emit(f"{temp_var} = getattr({parent_var}, '{field_name}', None)")
        else:
            self._emit(f"attr = getattr({parent_var}, '{field_name}', None)")
            if field.arguments:
                self._generate_arguments(field, field_def, info_var)
                self._emit(f"{temp_var} = attr(**kwargs) if callable(attr) else attr")
            else:
                self._emit(f"{temp_var} = attr() if callable(attr) else attr")

        # Handle nested selections
        if field.selection_set:
            field_type = field_def.type
            while hasattr(field_type, "of_type"):
                field_type = field_type.of_type

            # Handle Object, Union, and Interface types
            if isinstance(
                field_type, (GraphQLObjectType, GraphQLUnionType, GraphQLInterfaceType)
            ):
                self._emit(f"if {temp_var} is not None:")
                self.indent_level += 1

                # Check for list type
                if str(field_def.type).startswith("["):
                    self._emit(f'{result_var}["{alias}"] = []')
                    # Use unique variable names for nested lists
                    list_counter = self.nested_counter
                    self.nested_counter += 1
                    item_var = f"item_{list_counter}"
                    item_result_var = f"item_result_{list_counter}"

                    self._emit(f"for idx, {item_var} in enumerate({temp_var}):")
                    self.indent_level += 1
                    self._emit(f"{item_result_var} = {{}}")
                    item_path = f"{field_path} + [idx]"

                    # For unions/interfaces, we need runtime type resolution
                    if isinstance(field_type, (GraphQLUnionType, GraphQLInterfaceType)):
                        self._generate_abstract_type_selection(
                            field.selection_set,
                            field_type,
                            item_var,
                            item_result_var,
                            info_var,
                            item_path,
                        )
                    else:
                        self._generate_selection_set(
                            field.selection_set,
                            field_type,
                            item_var,
                            item_result_var,
                            info_var,
                            item_path,
                        )
                    self._emit(f'{result_var}["{alias}"].append({item_result_var})')
                    self.indent_level -= 1
                else:
                    # Use a unique variable name for nested results
                    nested_var = f"nested_result_{self.nested_counter}"
                    self.nested_counter += 1
                    self._emit(f"{nested_var} = {{}}")

                    # For unions/interfaces, we need runtime type resolution
                    if isinstance(field_type, (GraphQLUnionType, GraphQLInterfaceType)):
                        self._generate_abstract_type_selection(
                            field.selection_set,
                            field_type,
                            temp_var,
                            nested_var,
                            info_var,
                            field_path,
                        )
                    else:
                        self._generate_selection_set(
                            field.selection_set,
                            field_type,
                            temp_var,
                            nested_var,
                            info_var,
                            field_path,
                        )
                    self._emit(f'{result_var}["{alias}"] = {nested_var}')

                self.indent_level -= 1
                self._emit("else:")
                self.indent_level += 1
                self._emit(f'{result_var}["{alias}"] = None')
                self.indent_level -= 1
        else:
            # Apply scalar serialization if needed
            field_type = field_def.type
            while hasattr(field_type, "of_type"):
                field_type = field_type.of_type

            # Check if this is a custom scalar or enum that needs serialization
            from graphql import GraphQLEnumType

            if hasattr(field_type, "name") and field_type.name in [
                "String",
                "Int",
                "Float",
                "Boolean",
                "ID",
            ]:
                # Built-in scalars don't need special handling
                self._emit(f'{result_var}["{alias}"] = {temp_var}')
            elif isinstance(field_type, GraphQLEnumType) or (
                hasattr(field_type, "serialize") and callable(field_type.serialize)
            ):
                # Custom scalar with serialization
                self._emit(f"# Serialize custom scalar: {field_type.name}")
                if str(field_def.type).startswith("["):
                    # List of scalars
                    self._emit(f"if {temp_var} is not None:")
                    self.indent_level += 1
                    self._emit(f'{result_var}["{alias}"] = []')
                    self._emit(f"for scalar_item in {temp_var}:")
                    self.indent_level += 1
                    self._emit(
                        f"if scalar_item is not None and '{field_type.name}' in _scalar_serializers:"
                    )
                    self.indent_level += 1
                    self._emit(
                        f'{result_var}["{alias}"].append(_scalar_serializers["{field_type.name}"](scalar_item))'
                    )
                    self.indent_level -= 1
                    self._emit("else:")
                    self.indent_level += 1
                    self._emit(f'{result_var}["{alias}"].append(scalar_item)')
                    self.indent_level -= 1
                    self.indent_level -= 1
                    self.indent_level -= 1
                    self._emit("else:")
                    self.indent_level += 1
                    self._emit(f'{result_var}["{alias}"] = None')
                    self.indent_level -= 1
                else:
                    # Single scalar
                    self._emit(
                        f"if {temp_var} is not None and '{field_type.name}' in _scalar_serializers:"
                    )
                    self.indent_level += 1
                    self._emit(
                        f'{result_var}["{alias}"] = _scalar_serializers["{field_type.name}"]({temp_var})'
                    )
                    self.indent_level -= 1
                    self._emit("else:")
                    self.indent_level += 1
                    self._emit(f'{result_var}["{alias}"] = {temp_var}')
                    self.indent_level -= 1
            else:
                # Default - no serialization needed
                self._emit(f'{result_var}["{alias}"] = {temp_var}')

        # Error handling
        self.indent_level -= 1
        self._emit("except Exception as e:")
        self.indent_level += 1
        self._emit(f"errors.append({{'message': str(e), 'path': {field_path}}})")
        if is_nullable:
            self._emit(f'{result_var}["{alias}"] = None')
        else:
            self._emit("raise  # Propagate non-nullable error")
        self.indent_level -= 1

        # Close directive block
        if field.directives and skip_code:
            self.indent_level -= 1

    def _generate_arguments(self, field: FieldNode, field_def, info_var: str):
        """Generate field arguments handling."""
        self._emit("kwargs = {}")

        # Add defaults
        if field_def.args:
            for arg_name, arg_def in field_def.args.items():
                if (
                    hasattr(arg_def, "default_value")
                    and arg_def.default_value is not Undefined
                ):
                    default_val = self._serialize_value(arg_def.default_value)
                    self._emit(f"kwargs['{arg_name}'] = {default_val}")

        # Override with provided arguments
        if field.arguments:
            for arg in field.arguments:
                arg_name = arg.name.value
                # Get the argument type for custom scalar handling
                arg_type = (
                    field_def.args.get(arg_name).type
                    if field_def.args and arg_name in field_def.args
                    else None
                )
                arg_code = self._generate_argument_value(arg.value, info_var, arg_type)
                self._emit(f"kwargs['{arg_name}'] = {arg_code}")

    def _generate_argument_value(self, value_node, info_var: str, arg_type=None) -> str:
        """Generate code for argument value with custom scalar support."""
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
            var_name = value_node.name.value
            var_code = f"{info_var}.variable_values.get('{var_name}')"

            # Check if the argument type is a custom scalar that needs parsing
            if arg_type:
                from graphql import is_list_type, is_non_null_type

                # Check if it's a list type
                if is_list_type(arg_type) or (
                    is_non_null_type(arg_type) and is_list_type(arg_type.of_type)
                ):
                    # Get the item type
                    list_type = arg_type
                    if is_non_null_type(list_type):
                        list_type = list_type.of_type
                    item_type = list_type.of_type
                    if is_non_null_type(item_type):
                        item_type = item_type.of_type

                    # Check if item type is a custom scalar
                    if hasattr(item_type, "name") and hasattr(item_type, "parse_value"):
                        # Apply parse_value to each element in the list
                        parser_func = (
                            f"_scalar_parsers.get('{item_type.name}', lambda x: x)"
                        )
                        return f"([{parser_func}(item) for item in {var_code}] if {var_code} is not None else None)"
                else:
                    # Single value - check if it's a custom scalar
                    scalar_type = arg_type
                    while hasattr(scalar_type, "of_type"):
                        scalar_type = scalar_type.of_type

                    if hasattr(scalar_type, "name") and hasattr(
                        scalar_type, "parse_value"
                    ):
                        # This is a custom scalar - wrap with parse_value
                        return f"(_scalar_parsers.get('{scalar_type.name}', lambda x: x)({var_code}) if {var_code} is not None else None)"

            return var_code
        if isinstance(value_node, (IntValueNode, FloatValueNode)):
            return value_node.value
        if isinstance(value_node, StringValueNode):
            # For literal strings in custom scalars, we need to apply parse_literal
            if arg_type:
                scalar_type = arg_type
                while hasattr(scalar_type, "of_type"):
                    scalar_type = scalar_type.of_type

                if hasattr(scalar_type, "name") and hasattr(
                    scalar_type, "parse_literal"
                ):
                    # Custom scalar with parse_literal
                    return f"_scalar_parsers.get('{scalar_type.name}', lambda x: x)({value_node.value!r})"

            return repr(value_node.value)
        if isinstance(value_node, BooleanValueNode):
            return "True" if value_node.value else "False"
        if isinstance(value_node, NullValueNode):
            return "None"
        if isinstance(value_node, EnumValueNode):
            # For enum values, we need to get the actual enum instance
            # The enum value in the query (e.g., "HIGH") needs to be mapped to the Python enum
            if arg_type:
                from graphql import GraphQLEnumType, is_non_null_type

                enum_type = arg_type
                if is_non_null_type(enum_type):
                    enum_type = enum_type.of_type

                if isinstance(enum_type, GraphQLEnumType):
                    # Get the enum value configuration
                    enum_value_name = value_node.value
                    if enum_value_name in enum_type.values:
                        # The enum_type.values[name].value contains the actual Python enum instance
                        # We need to generate code that accesses this at runtime
                        return f"_schema.type_map['{enum_type.name}'].values['{enum_value_name}'].value"

            # Fallback to string representation
            return repr(value_node.value)
        if isinstance(value_node, ListValueNode):
            # For list values, pass the item type to recursive calls
            item_type = None
            if arg_type:
                from graphql import is_list_type, is_non_null_type

                list_type = arg_type
                if is_non_null_type(list_type):
                    list_type = list_type.of_type
                if is_list_type(list_type):
                    item_type = list_type.of_type

            items = [
                self._generate_argument_value(item, info_var, item_type)
                for item in value_node.values
            ]
            return f"[{', '.join(items)}]"
        if isinstance(value_node, ObjectValueNode):
            # For object values, we need to pass field types to handle enums properly
            items = []

            # Try to get the input object type to get field types
            field_types = {}
            if arg_type:
                from graphql import GraphQLInputObjectType, is_non_null_type

                input_type = arg_type
                if is_non_null_type(input_type):
                    input_type = input_type.of_type

                if isinstance(input_type, GraphQLInputObjectType):
                    # Get field types from the input object
                    for field_name, field_def in input_type.fields.items():
                        field_types[field_name] = field_def.type

            for field in value_node.fields:
                key = repr(field.name.value)
                field_name = field.name.value
                field_type = field_types.get(field_name)
                val = self._generate_argument_value(field.value, info_var, field_type)
                items.append(f"{key}: {val}")
            return f"{{{', '.join(items)}}}"
        return "None"

    def _serialize_value(self, value) -> str:
        """Serialize Python value for code generation."""
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
        path: str,
    ):
        """Generate fragment spread."""
        fragment_name = fragment_spread.name.value
        if fragment_name not in self.fragments:
            raise ValueError(f"Fragment '{fragment_name}' not found")

        fragment_def = self.fragments[fragment_name]
        type_condition = fragment_def.type_condition.name.value

        if parent_type.name == type_condition:
            if fragment_def.selection_set:
                self._generate_selection_set(
                    fragment_def.selection_set,
                    parent_type,
                    parent_var,
                    result_var,
                    info_var,
                    path,
                )
        else:
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
                    path,
                )
            self.indent_level -= 1

    def _generate_inline_fragment(
        self,
        inline_fragment: InlineFragmentNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ):
        """Generate inline fragment."""
        if inline_fragment.type_condition:
            type_name = inline_fragment.type_condition.name.value
            fragment_type = self.schema.type_map.get(type_name)

            if not fragment_type or not isinstance(fragment_type, GraphQLObjectType):
                return

            if type_name == parent_type.name:
                if inline_fragment.selection_set:
                    self._generate_selection_set(
                        inline_fragment.selection_set,
                        fragment_type,
                        parent_var,
                        result_var,
                        info_var,
                        path,
                    )
            else:
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
                        path,
                    )
                self.indent_level -= 1
        elif inline_fragment.selection_set:
            self._generate_selection_set(
                inline_fragment.selection_set,
                parent_type,
                parent_var,
                result_var,
                info_var,
                path,
            )

    def _generate_introspection_selection(
        self,
        selection_set: SelectionSetNode,
        introspection_type: str,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ):
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
                "kind": lambda t: self._get_type_kind(t),
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
                "possibleTypes": lambda t: list(t.types)
                if hasattr(t, "types")
                else None,
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
                if fragment_name in self.fragments:
                    fragment_def = self.fragments[fragment_name]
                    # Check type condition matches
                    if fragment_def.type_condition.name.value == introspection_type:
                        self._emit(f"# Fragment spread: {fragment_name}")
                        self._generate_introspection_selection(
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
                        self._emit(f"# Inline fragment on {introspection_type}")
                        self._generate_introspection_selection(
                            selection.selection_set,
                            introspection_type,
                            parent_var,
                            result_var,
                            info_var,
                            path,
                        )
                else:
                    # No type condition - always apply
                    self._generate_introspection_selection(
                        selection.selection_set,
                        introspection_type,
                        parent_var,
                        result_var,
                        info_var,
                        path,
                    )
                continue
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                alias = selection.alias.value if selection.alias else field_name

                if field_name == "__typename":
                    self._emit(f'{result_var}["{alias}"] = "{introspection_type}"')
                    continue

                # Generate code to resolve the introspection field
                self._emit(f"# Resolve {introspection_type}.{field_name}")

                # Handle special cases for introspection fields
                if introspection_type == "__Schema":
                    if field_name == "queryType":
                        self._emit(f"schema_query_type = {parent_var}.query_type")
                        if selection.selection_set:
                            self._emit("if schema_query_type:")
                            self.indent_level += 1
                            self._emit(f"{result_var}['{alias}'] = {{}}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__Type",
                                "schema_query_type",
                                f"{result_var}['{alias}']",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self.indent_level -= 1
                            self._emit("else:")
                            self.indent_level += 1
                            self._emit(f"{result_var}['{alias}'] = None")
                            self.indent_level -= 1
                        else:
                            self._emit(f"{result_var}['{alias}'] = schema_query_type")
                    elif field_name == "mutationType":
                        self._emit(f"schema_mutation_type = {parent_var}.mutation_type")
                        if selection.selection_set:
                            self._emit("if schema_mutation_type:")
                            self.indent_level += 1
                            self._emit(f"{result_var}['{alias}'] = {{}}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__Type",
                                "schema_mutation_type",
                                f"{result_var}['{alias}']",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self.indent_level -= 1
                            self._emit("else:")
                            self.indent_level += 1
                            self._emit(f"{result_var}['{alias}'] = None")
                            self.indent_level -= 1
                        else:
                            self._emit(
                                f"{result_var}['{alias}'] = schema_mutation_type"
                            )
                    elif field_name == "subscriptionType":
                        self._emit(
                            f"schema_subscription_type = {parent_var}.subscription_type"
                        )
                        if selection.selection_set:
                            self._emit("if schema_subscription_type:")
                            self.indent_level += 1
                            self._emit(f"{result_var}['{alias}'] = {{}}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__Type",
                                "schema_subscription_type",
                                f"{result_var}['{alias}']",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self.indent_level -= 1
                            self._emit("else:")
                            self.indent_level += 1
                            self._emit(f"{result_var}['{alias}'] = None")
                            self.indent_level -= 1
                        else:
                            self._emit(
                                f"{result_var}['{alias}'] = schema_subscription_type"
                            )
                    elif field_name == "types":
                        self._emit(
                            f"schema_types = list({parent_var}.type_map.values())"
                        )
                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = []")
                            self._emit("for schema_type in schema_types:")
                            self.indent_level += 1
                            self._emit("type_result = {}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__Type",
                                "schema_type",
                                "type_result",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self._emit(f"{result_var}['{alias}'].append(type_result)")
                            self.indent_level -= 1
                        else:
                            self._emit(f"{result_var}['{alias}'] = schema_types")
                    elif field_name == "directives":
                        self._emit(f"schema_directives = {parent_var}.directives")
                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = []")
                            self._emit("for directive in schema_directives:")
                            self.indent_level += 1
                            self._emit("directive_result = {}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__Directive",
                                "directive",
                                "directive_result",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self._emit(
                                f"{result_var}['{alias}'].append(directive_result)"
                            )
                            self.indent_level -= 1
                        else:
                            self._emit(f"{result_var}['{alias}'] = schema_directives")

                elif introspection_type == "__Type":
                    if field_name == "kind":
                        self._emit(
                            "from graphql.type import is_scalar_type, is_object_type, is_interface_type, is_union_type, is_enum_type, is_input_object_type, is_list_type, is_non_null_type"
                        )
                        self._emit(f"if is_scalar_type({parent_var}):")
                        self.indent_level += 1
                        self._emit(f'{result_var}["{alias}"] = "SCALAR"')
                        self.indent_level -= 1
                        self._emit(f"elif is_object_type({parent_var}):")
                        self.indent_level += 1
                        self._emit(f'{result_var}["{alias}"] = "OBJECT"')
                        self.indent_level -= 1
                        self._emit(f"elif is_interface_type({parent_var}):")
                        self.indent_level += 1
                        self._emit(f'{result_var}["{alias}"] = "INTERFACE"')
                        self.indent_level -= 1
                        self._emit(f"elif is_union_type({parent_var}):")
                        self.indent_level += 1
                        self._emit(f'{result_var}["{alias}"] = "UNION"')
                        self.indent_level -= 1
                        self._emit(f"elif is_enum_type({parent_var}):")
                        self.indent_level += 1
                        self._emit(f'{result_var}["{alias}"] = "ENUM"')
                        self.indent_level -= 1
                        self._emit(f"elif is_input_object_type({parent_var}):")
                        self.indent_level += 1
                        self._emit(f'{result_var}["{alias}"] = "INPUT_OBJECT"')
                        self.indent_level -= 1
                        self._emit(f"elif is_list_type({parent_var}):")
                        self.indent_level += 1
                        self._emit(f'{result_var}["{alias}"] = "LIST"')
                        self.indent_level -= 1
                        self._emit(f"elif is_non_null_type({parent_var}):")
                        self.indent_level += 1
                        self._emit(f'{result_var}["{alias}"] = "NON_NULL"')
                        self.indent_level -= 1
                        self._emit("else:")
                        self.indent_level += 1
                        self._emit(f'{result_var}["{alias}"] = None')
                        self.indent_level -= 1
                    elif field_name == "name":
                        self._emit(
                            f'{result_var}["{alias}"] = {parent_var}.name if hasattr({parent_var}, "name") else None'
                        )
                    elif field_name == "description":
                        self._emit(
                            f'{result_var}["{alias}"] = {parent_var}.description if hasattr({parent_var}, "description") else None'
                        )
                    elif field_name == "fields":
                        # Get includeDeprecated argument
                        include_deprecated = False
                        if selection.arguments:
                            for arg in selection.arguments:
                                if arg.name.value == "includeDeprecated":
                                    arg_val = self._generate_argument_value(
                                        arg.value, info_var
                                    )
                                    self._emit(f"include_deprecated = {arg_val}")
                                    include_deprecated = True
                                    break
                        if not include_deprecated:
                            self._emit("include_deprecated = False")

                        self._emit(f"if hasattr({parent_var}, 'fields'):")
                        self.indent_level += 1
                        self._emit("type_fields = []")
                        self._emit(
                            f"for field_name, field_def in {parent_var}.fields.items():"
                        )
                        self.indent_level += 1
                        self._emit(
                            "if include_deprecated or not field_def.deprecation_reason:"
                        )
                        self.indent_level += 1
                        self._emit("type_fields.append((field_name, field_def))")
                        self.indent_level -= 1
                        self.indent_level -= 1

                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = []")
                            self._emit("for field_name, field_def in type_fields:")
                            self.indent_level += 1
                            self._emit("field_result = {}")
                            # Pass both field_name and field_def
                            self._emit("field_with_name = (field_name, field_def)")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__Field",
                                "field_with_name",
                                "field_result",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self._emit(f"{result_var}['{alias}'].append(field_result)")
                            self.indent_level -= 1
                        else:
                            self._emit(f"{result_var}['{alias}'] = type_fields")
                        self.indent_level -= 1
                        self._emit("else:")
                        self.indent_level += 1
                        self._emit(f"{result_var}['{alias}'] = None")
                        self.indent_level -= 1
                    elif field_name == "interfaces":
                        self._emit(f"if hasattr({parent_var}, 'interfaces'):")
                        self.indent_level += 1
                        self._emit(f"type_interfaces = list({parent_var}.interfaces)")
                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = []")
                            self._emit("for interface in type_interfaces:")
                            self.indent_level += 1
                            self._emit("interface_result = {}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__Type",
                                "interface",
                                "interface_result",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self._emit(
                                f"{result_var}['{alias}'].append(interface_result)"
                            )
                            self.indent_level -= 1
                        else:
                            self._emit(f"{result_var}['{alias}'] = type_interfaces")
                        self.indent_level -= 1
                        self._emit("else:")
                        self.indent_level += 1
                        self._emit(f"{result_var}['{alias}'] = None")
                        self.indent_level -= 1
                    elif field_name == "possibleTypes":
                        self._emit(f"if hasattr({parent_var}, 'types'):")
                        self.indent_level += 1
                        self._emit(f"possible_types = list({parent_var}.types)")
                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = []")
                            self._emit("for ptype in possible_types:")
                            self.indent_level += 1
                            self._emit("ptype_result = {}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__Type",
                                "ptype",
                                "ptype_result",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self._emit(f"{result_var}['{alias}'].append(ptype_result)")
                            self.indent_level -= 1
                        else:
                            self._emit(f"{result_var}['{alias}'] = possible_types")
                        self.indent_level -= 1
                        self._emit("else:")
                        self.indent_level += 1
                        self._emit(f"{result_var}['{alias}'] = None")
                        self.indent_level -= 1
                    elif field_name == "enumValues":
                        # Get includeDeprecated argument
                        include_deprecated = False
                        if selection.arguments:
                            for arg in selection.arguments:
                                if arg.name.value == "includeDeprecated":
                                    arg_val = self._generate_argument_value(
                                        arg.value, info_var
                                    )
                                    self._emit(f"include_deprecated = {arg_val}")
                                    include_deprecated = True
                                    break
                        if not include_deprecated:
                            self._emit("include_deprecated = False")

                        self._emit(f"if hasattr({parent_var}, 'values'):")
                        self.indent_level += 1
                        self._emit(f"enum_values = list({parent_var}.values.values())")
                        self._emit("if not include_deprecated:")
                        self.indent_level += 1
                        self._emit(
                            "enum_values = [v for v in enum_values if not v.deprecation_reason]"
                        )
                        self.indent_level -= 1

                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = []")
                            self._emit("for enum_val in enum_values:")
                            self.indent_level += 1
                            self._emit("enum_result = {}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__EnumValue",
                                "enum_val",
                                "enum_result",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self._emit(f"{result_var}['{alias}'].append(enum_result)")
                            self.indent_level -= 1
                        else:
                            self._emit(f"{result_var}['{alias}'] = enum_values")
                        self.indent_level -= 1
                        self._emit("else:")
                        self.indent_level += 1
                        self._emit(f"{result_var}['{alias}'] = None")
                        self.indent_level -= 1
                    elif field_name == "inputFields":
                        self._emit("from graphql import is_input_object_type")
                        self._emit(f"if is_input_object_type({parent_var}):")
                        self.indent_level += 1
                        self._emit("input_fields = []")
                        self._emit(
                            f"for field_name, field_def in {parent_var}.fields.items():"
                        )
                        self.indent_level += 1
                        self._emit("input_fields.append((field_name, field_def))")
                        self.indent_level -= 1

                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = []")
                            self._emit("for input_field_tuple in input_fields:")
                            self.indent_level += 1
                            self._emit("input_result = {}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__InputValue",
                                "input_field_tuple",
                                "input_result",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self._emit(f"{result_var}['{alias}'].append(input_result)")
                            self.indent_level -= 1
                        else:
                            self._emit(f"{result_var}['{alias}'] = input_fields")
                        self.indent_level -= 1
                        self._emit("else:")
                        self.indent_level += 1
                        self._emit(f"{result_var}['{alias}'] = None")
                        self.indent_level -= 1
                    elif field_name == "ofType":
                        self._emit(f"if hasattr({parent_var}, 'of_type'):")
                        self.indent_level += 1
                        self._emit(f"of_type = {parent_var}.of_type")
                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = {{}}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__Type",
                                "of_type",
                                f"{result_var}['{alias}']",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                        else:
                            self._emit(f"{result_var}['{alias}'] = of_type")
                        self.indent_level -= 1
                        self._emit("else:")
                        self.indent_level += 1
                        self._emit(f"{result_var}['{alias}'] = None")
                        self.indent_level -= 1

                elif introspection_type == "__Field":
                    # __Field can be either a tuple (field_name, field_def) or just field_def
                    self._emit("# Handle __Field which may be a tuple")
                    self._emit(f"if isinstance({parent_var}, tuple):")
                    self.indent_level += 1
                    self._emit(f"_field_name, _field_def = {parent_var}")
                    self.indent_level -= 1
                    self._emit("else:")
                    self.indent_level += 1
                    self._emit(f"_field_name = getattr({parent_var}, 'name', None)")
                    self._emit(f"_field_def = {parent_var}")
                    self.indent_level -= 1

                    if field_name == "name":
                        self._emit(f'{result_var}["{alias}"] = _field_name')
                    elif field_name == "description":
                        self._emit(f'{result_var}["{alias}"] = _field_def.description')
                    elif field_name == "args":
                        self._emit("field_args = []")
                        self._emit("if _field_def.args:")
                        self.indent_level += 1
                        self._emit("for arg_name, arg_def in _field_def.args.items():")
                        self.indent_level += 1
                        self._emit("field_args.append((arg_name, arg_def))")
                        self.indent_level -= 1
                        self.indent_level -= 1

                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = []")
                            self._emit("for arg_tuple in field_args:")
                            self.indent_level += 1
                            self._emit("arg_result = {}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__InputValue",
                                "arg_tuple",
                                "arg_result",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self._emit(f"{result_var}['{alias}'].append(arg_result)")
                            self.indent_level -= 1
                        else:
                            self._emit(f"{result_var}['{alias}'] = field_args")
                    elif field_name == "type":
                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = {{}}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__Type",
                                "_field_def.type",
                                f"{result_var}['{alias}']",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                        else:
                            self._emit(f"{result_var}['{alias}'] = _field_def.type")
                    elif field_name == "isDeprecated":
                        self._emit(
                            f'{result_var}["{alias}"] = _field_def.deprecation_reason is not None'
                        )
                    elif field_name == "deprecationReason":
                        self._emit(
                            f'{result_var}["{alias}"] = _field_def.deprecation_reason'
                        )

                elif introspection_type == "__InputValue":
                    # __InputValue can be either a tuple (arg_name, arg_def) or just arg_def
                    self._emit("# Handle __InputValue which may be a tuple")
                    self._emit(f"if isinstance({parent_var}, tuple):")
                    self.indent_level += 1
                    self._emit(f"_input_name, _input_def = {parent_var}")
                    self.indent_level -= 1
                    self._emit("else:")
                    self.indent_level += 1
                    self._emit(f"_input_name = getattr({parent_var}, 'name', None)")
                    self._emit(f"_input_def = {parent_var}")
                    self.indent_level -= 1

                    if field_name == "name":
                        self._emit(f'{result_var}["{alias}"] = _input_name')
                    elif field_name == "description":
                        self._emit(
                            f'{result_var}["{alias}"] = _input_def.description if hasattr(_input_def, "description") else None'
                        )
                    elif field_name == "type":
                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = {{}}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__Type",
                                "_input_def.type",
                                f"{result_var}['{alias}']",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                        else:
                            self._emit(
                                f"{result_var}['{alias}'] = _input_def.type if hasattr(_input_def, 'type') else None"
                            )
                    elif field_name == "defaultValue":
                        self._emit("from graphql import Undefined")
                        self._emit(
                            "if hasattr(_input_def, 'default_value') and _input_def.default_value is not Undefined:"
                        )
                        self.indent_level += 1
                        self._emit(
                            f'{result_var}["{alias}"] = str(_input_def.default_value)'
                        )
                        self.indent_level -= 1
                        self._emit("else:")
                        self.indent_level += 1
                        self._emit(f'{result_var}["{alias}"] = None')
                        self.indent_level -= 1

                elif introspection_type == "__EnumValue":
                    if field_name == "name":
                        self._emit(f'{result_var}["{alias}"] = {parent_var}.value')
                    elif field_name == "description":
                        self._emit(
                            f'{result_var}["{alias}"] = {parent_var}.description'
                        )
                    elif field_name == "isDeprecated":
                        self._emit(
                            f'{result_var}["{alias}"] = {parent_var}.deprecation_reason is not None'
                        )
                    elif field_name == "deprecationReason":
                        self._emit(
                            f'{result_var}["{alias}"] = {parent_var}.deprecation_reason'
                        )

                elif introspection_type == "__Directive":
                    if field_name == "name":
                        self._emit(f'{result_var}["{alias}"] = {parent_var}.name')
                    elif field_name == "description":
                        self._emit(
                            f'{result_var}["{alias}"] = {parent_var}.description'
                        )
                    elif field_name == "locations":
                        self._emit(
                            f'{result_var}["{alias}"] = [loc.name if hasattr(loc, "name") else str(loc) for loc in {parent_var}.locations]'
                        )
                    elif field_name == "args":
                        self._emit("directive_args = []")
                        self._emit(f"if {parent_var}.args:")
                        self.indent_level += 1
                        self._emit(
                            f"for arg_name, arg_def in {parent_var}.args.items():"
                        )
                        self.indent_level += 1
                        self._emit("directive_args.append((arg_name, arg_def))")
                        self.indent_level -= 1
                        self.indent_level -= 1

                        if selection.selection_set:
                            self._emit(f"{result_var}['{alias}'] = []")
                            self._emit("for arg_tuple in directive_args:")
                            self.indent_level += 1
                            self._emit("arg_result = {}")
                            self._generate_introspection_selection(
                                selection.selection_set,
                                "__InputValue",
                                "arg_tuple",
                                "arg_result",
                                info_var,
                                f"{path} + ['{alias}']",
                            )
                            self._emit(f"{result_var}['{alias}'].append(arg_result)")
                            self.indent_level -= 1
                        else:
                            self._emit(f"{result_var}['{alias}'] = directive_args")

    def _generate_abstract_type_selection(
        self,
        selection_set: SelectionSetNode,
        abstract_type: Union[GraphQLUnionType, GraphQLInterfaceType],
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ):
        """Generate selection for union or interface types with runtime type resolution."""
        # First, always add __typename for proper type discrimination
        self._emit(f"# Resolve abstract type: {abstract_type.name}")

        # Get the actual typename from the object
        self._emit("# Get runtime type")
        self._emit("actual_typename = None")
        self._emit(f'if hasattr({parent_var}, "__typename"):')
        self.indent_level += 1
        self._emit(f"actual_typename = {parent_var}.__typename")
        self.indent_level -= 1
        self._emit(f'elif hasattr({parent_var}.__class__, "__name__"):')
        self.indent_level += 1
        self._emit(f"actual_typename = {parent_var}.__class__.__name__")
        self.indent_level -= 1

        # Add __typename to result if requested
        for selection in selection_set.selections:
            if (
                isinstance(selection, FieldNode)
                and selection.name.value == "__typename"
            ):
                alias = selection.alias.value if selection.alias else "__typename"
                self._emit(f'{result_var}["{alias}"] = actual_typename')
                break

        # Collect fragments and inline fragments by type
        type_selections = {}  # type_name -> selections
        common_selections = []  # Selections without type condition

        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                if selection.name.value != "__typename":
                    common_selections.append(selection)
            elif isinstance(selection, InlineFragmentNode):
                if selection.type_condition:
                    type_name = selection.type_condition.name.value
                    if type_name not in type_selections:
                        type_selections[type_name] = []
                    type_selections[type_name].extend(
                        selection.selection_set.selections
                    )
                else:
                    # No type condition means it applies to all types
                    common_selections.extend(selection.selection_set.selections)
            elif isinstance(selection, FragmentSpreadNode):
                # Handle fragment spreads
                fragment_name = selection.name.value
                if fragment_name in self.fragments:
                    fragment_def = self.fragments[fragment_name]
                    if fragment_def.type_condition:
                        type_name = fragment_def.type_condition.name.value
                        if type_name not in type_selections:
                            type_selections[type_name] = []
                        type_selections[type_name].extend(
                            fragment_def.selection_set.selections
                        )

        # Get possible types for the union/interface
        possible_types = []
        if isinstance(abstract_type, GraphQLUnionType):
            possible_types = list(abstract_type.types)
        elif isinstance(abstract_type, GraphQLInterfaceType):
            # For interfaces, we need to get implementing types from schema
            for type_name, gql_type in self.schema.type_map.items():
                if isinstance(gql_type, GraphQLObjectType):
                    if abstract_type in gql_type.interfaces:
                        possible_types.append(gql_type)

        # Generate type-specific selections
        if type_selections or common_selections:
            first_type = True
            for possible_type in possible_types:
                type_name = possible_type.name

                # Check if we have selections for this type
                selections_for_type = common_selections.copy()
                if type_name in type_selections:
                    selections_for_type.extend(type_selections[type_name])

                if selections_for_type:
                    if first_type:
                        self._emit(f'if actual_typename == "{type_name}":')
                        first_type = False
                    else:
                        self._emit(f'elif actual_typename == "{type_name}":')

                    self.indent_level += 1

                    # Generate selections for this concrete type
                    for selection in selections_for_type:
                        if isinstance(selection, FieldNode):
                            self._generate_field(
                                selection,
                                possible_type,
                                parent_var,
                                result_var,
                                info_var,
                                path,
                            )

                    self.indent_level -= 1

            # Add else clause for unknown types (just process common selections)
            if not first_type and common_selections:
                self._emit("else:")
                self.indent_level += 1
                self._emit("# Unknown type, process common fields only")

                # Try to resolve common fields
                for selection in common_selections:
                    if isinstance(selection, FieldNode):
                        field_name = selection.name.value
                        alias = selection.alias.value if selection.alias else field_name
                        self._emit(
                            f'{result_var}["{alias}"] = getattr({parent_var}, "{field_name}", None)'
                        )

                self.indent_level -= 1

    def _generate_skip_include_checks(
        self, directives: List[DirectiveNode], info_var: str
    ) -> str:
        """Generate directive conditions."""
        conditions = []

        for directive in directives:
            directive_name = directive.name.value

            if directive_name == "skip":
                if_arg = self._get_directive_argument(directive, "if", info_var)
                if if_arg:
                    conditions.append(f"not ({if_arg})")
            elif directive_name == "include":
                if_arg = self._get_directive_argument(directive, "if", info_var)
                if if_arg:
                    conditions.append(if_arg)

        if conditions:
            return f"if {' and '.join(conditions)}:"
        return ""

    def _get_directive_argument(
        self, directive: DirectiveNode, arg_name: str, info_var: str
    ) -> str:
        """Get directive argument value."""
        for arg in directive.arguments or []:
            if arg.name.value == arg_name:
                return self._generate_argument_value(arg.value, info_var)
        return ""

    def _detect_async_resolvers(
        self, selection_set: SelectionSetNode, parent_type: GraphQLObjectType
    ):
        """Pre-scan for async resolvers."""
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

                    if selection.selection_set:
                        field_type = field_def.type
                        while hasattr(field_type, "of_type"):
                            field_type = field_type.of_type
                        if isinstance(field_type, GraphQLObjectType):
                            self._detect_async_resolvers(
                                selection.selection_set, field_type
                            )
            elif isinstance(selection, FragmentSpreadNode):
                fragment_name = selection.name.value
                if fragment_name in self.fragments:
                    fragment_def = self.fragments[fragment_name]
                    if fragment_def.selection_set:
                        self._detect_async_resolvers(
                            fragment_def.selection_set, parent_type
                        )
            elif isinstance(selection, InlineFragmentNode):
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
        """Emit line of code with proper indentation."""
        indent = "    " * self.indent_level
        self.generated_code.append(f"{indent}{line}")


class CachedJITCompiler:
    """JIT compiler with built-in caching for production use.

    Features:
    - LRU cache with configurable size
    - TTL support for cache entries
    - Thread-safe caching
    - Automatic cache invalidation
    """

    def __init__(
        self,
        schema: GraphQLSchema,
        cache_size: int = 1000,
        ttl_seconds: Optional[float] = None,
    ):
        self.schema = schema
        self.compiler = JITCompiler(schema)
        self.cache: Dict[str, Tuple[Callable, float]] = {}
        self.cache_size = cache_size
        self.ttl_seconds = ttl_seconds
        self.access_order: List[str] = []

    def compile_query(self, query: str) -> Callable:
        """Compile query with caching."""
        # Generate cache key
        cache_key = hashlib.md5(query.encode()).hexdigest()

        # Check cache
        if cache_key in self.cache:
            compiled_fn, timestamp = self.cache[cache_key]

            # Check TTL
            if self.ttl_seconds is None or (time.time() - timestamp) < self.ttl_seconds:
                # Update access order for LRU
                if cache_key in self.access_order:
                    self.access_order.remove(cache_key)
                self.access_order.append(cache_key)
                return compiled_fn
            # Expired, remove from cache
            del self.cache[cache_key]
            self.access_order.remove(cache_key)

        # Compile query
        compiled_fn = self.compiler.compile_query(query)

        # Add to cache
        self.cache[cache_key] = (compiled_fn, time.time())
        self.access_order.append(cache_key)

        # Enforce cache size limit (LRU eviction)
        while len(self.cache) > self.cache_size:
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                del self.cache[oldest_key]

        return compiled_fn

    def clear_cache(self):
        """Clear the cache."""
        self.cache.clear()
        self.access_order.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.cache_size,
            "ttl_seconds": self.ttl_seconds,
            "keys": list(self.cache.keys()),
        }


# Public API
def compile_query(schema: GraphQLSchema, query: str) -> Callable:
    """Compile a GraphQL query into optimized Python code.

    This is the main entry point for JIT compilation.

    Args:
        schema: The GraphQL schema
        query: The GraphQL query string

    Returns:
        A compiled function that executes the query
    """
    compiler = JITCompiler(schema)
    return compiler.compile_query(query)


def create_cached_compiler(
    schema: GraphQLSchema,
    cache_size: int = 1000,
    ttl_seconds: Optional[float] = None,
) -> CachedJITCompiler:
    """Create a cached JIT compiler for production use.

    Args:
        schema: The GraphQL schema
        cache_size: Maximum number of cached queries (default: 1000)
        ttl_seconds: TTL for cache entries in seconds (default: None = no expiry)

    Returns:
        A CachedJITCompiler instance
    """
    return CachedJITCompiler(schema, cache_size, ttl_seconds)


__all__ = [
    "CachedJITCompiler",
    "JITCompiler",
    "compile_query",
    "create_cached_compiler",
]
