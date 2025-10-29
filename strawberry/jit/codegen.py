"""Code generation for JIT compiler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from graphql import (
    FieldNode,
    FragmentSpreadNode,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLType,
    GraphQLUnionType,
    InlineFragmentNode,
    SelectionSetNode,
    Undefined,
)

if TYPE_CHECKING:
    from graphql.language import OperationDefinitionNode, ValueNode

    from .compiler import JITCompiler


class CodeGenerator:
    """Generates optimized Python code from GraphQL AST."""

    def __init__(self, compiler: JITCompiler) -> None:
        self.compiler = compiler

    def generate_optimized_function(
        self, operation: OperationDefinitionNode, root_type: GraphQLObjectType
    ) -> str:
        """Generate optimized function with all performance enhancements."""
        self.compiler.generated_code = []
        self.compiler.indent_level = 0

        # Add imports
        self.compiler._emit("from typing import Any, Dict, List, Optional")
        self.compiler._emit("")

        # Check if this is a mutation (mutations must execute serially)
        from graphql.language import OperationType

        is_mutation = operation.operation == OperationType.MUTATION

        # Pre-scan for async resolvers
        if operation.selection_set:
            self.compiler._detect_async_resolvers(operation.selection_set, root_type)

        if self.compiler.has_async_resolvers:
            self.compiler._emit("import asyncio")
            self.compiler._emit("import inspect")
            self.compiler._emit("")

        # Generate function signature
        if self.compiler.has_async_resolvers:
            self.compiler._emit(
                "async def execute_query(root, context=None, variables=None):"
            )
        else:
            self.compiler._emit(
                "def execute_query(root, context=None, variables=None):"
            )

        self.compiler.indent_level += 1
        self.compiler._emit(
            '"""Execute JIT-compiled GraphQL query with optimizations."""'
        )
        self.compiler._emit("result = {}")
        self.compiler._emit("errors = []")

        # Coerce variables to handle enums and other input types properly
        if operation.variable_definitions:
            self.compiler._emit("# Coerce variables")
            self.compiler._emit(
                "from graphql.execution.values import get_variable_values"
            )
            self.compiler._emit(
                "coerced = get_variable_values(_schema, _var_defs, variables or {})"
            )
            self.compiler._emit("if isinstance(coerced, list):")  # List means errors
            self.compiler.indent_level += 1
            self.compiler._emit("for error in coerced:")
            self.compiler.indent_level += 1
            self.compiler._emit("errors.append({'message': str(error), 'path': []})")
            self.compiler.indent_level -= 1
            self.compiler._emit('return {"data": None, "errors": errors}')
            self.compiler.indent_level -= 1
            self.compiler._emit("variables = coerced")  # Dict of coerced values
        else:
            self.compiler._emit("variables = variables or {}")

        # Create mock info object
        self.compiler._emit("")
        self.compiler._emit("info = _MockInfo(_schema)")
        self.compiler._emit("info.root_value = root")
        self.compiler._emit("info.context = context")
        self.compiler._emit("info.variable_values = variables")
        self.compiler._emit("")

        # Generate selection set with error handling
        if operation.selection_set:
            self.compiler._emit("# Execute query with error handling")
            self.compiler._emit("try:")
            self.compiler.indent_level += 1

            # Mutations MUST execute serially per GraphQL spec
            # Queries can use parallel execution for performance
            if (
                self.compiler.enable_parallel
                and self.compiler.has_async_resolvers
                and not is_mutation
            ):
                self.compiler._emit("# Parallel execution for query fields")
                self.generate_parallel_selection_set(
                    operation.selection_set, root_type, "root", "result", "info", "[]"
                )
            else:
                if is_mutation:
                    self.compiler._emit(
                        "# Serial execution for mutations (GraphQL spec requirement)"
                    )
                self.generate_selection_set(
                    operation.selection_set, root_type, "root", "result", "info", "[]"
                )

            self.compiler.indent_level -= 1
            self.compiler._emit("except Exception as root_error:")
            self.compiler.indent_level += 1
            # Don't add error if it already exists (from field-level handling)
            # Just null the result since a non-null field errored
            self.compiler._emit("result = None")
            self.compiler.indent_level -= 1

        self.compiler._emit("")
        self.compiler._emit("# Return result with errors if any")
        self.compiler._emit("if errors:")
        self.compiler.indent_level += 1
        self.compiler._emit('return {"data": result, "errors": errors}')
        self.compiler.indent_level -= 1
        self.compiler._emit('return {"data": result}')

        return "\n".join(self.compiler.generated_code)

    def is_field_async(self, field_def: GraphQLField) -> bool:
        """Check if a field is async using StrawberryField metadata.

        This uses compile-time information from Strawberry's field decoration
        instead of runtime introspection, improving performance.
        """
        # First try to get the StrawberryField from extensions
        if hasattr(field_def, "extensions") and field_def.extensions:
            strawberry_field = field_def.extensions.get("strawberry-definition")
            if strawberry_field and hasattr(strawberry_field, "is_async"):
                return strawberry_field.is_async

        # Fallback to runtime check if StrawberryField not available
        # (e.g., for built-in GraphQL fields)
        if field_def.resolve:
            import inspect

            return inspect.iscoroutinefunction(field_def.resolve)
        return False

    def generate_parallel_selection_set(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Generate selection set with parallel async execution."""
        # Check if we should use parallel execution based on depth
        # Deep nesting with parallel execution creates exponential overhead
        use_parallel = (
            self.compiler.enable_parallel
            and self.compiler.parallel_depth < self.compiler.max_parallel_depth
        )

        if not use_parallel:
            # Fall back to sequential execution at deep nesting levels
            return self.generate_selection_set(
                selection_set, parent_type, parent_var, result_var, info_var, path
            )

        # Track depth for nested calls
        self.compiler.parallel_depth += 1

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
                    resolver_id = f"resolver_{self.compiler.field_counter}"
                    self.compiler.field_counter += 1

                    # Use compile-time async detection from StrawberryField
                    if self.is_field_async(field_def):
                        async_fields.append((selection, resolver_id))
                        if field_def.resolve:
                            self.compiler.resolver_map[resolver_id] = field_def.resolve
                        self.compiler.async_resolver_ids.add(resolver_id)
                    else:
                        sync_fields.append(selection)
                        if field_def.resolve:
                            self.compiler.resolver_map[resolver_id] = field_def.resolve
            else:
                fragments.append(selection)

        # Execute sync fields first
        for selection in sync_fields:
            self.generate_field(
                selection, parent_type, parent_var, result_var, info_var, path
            )

        # Execute async fields in parallel if multiple
        if len(async_fields) > 1:
            # Use unique variable names to avoid shadowing in nested contexts
            gather_id = self.compiler.nested_counter
            self.compiler.nested_counter += 1
            tasks_var = f"async_tasks_{gather_id}"
            results_var = f"async_results_{gather_id}"
            result_item_var = f"async_result_{gather_id}"

            self.compiler._emit("# Execute async fields in parallel")
            self.compiler._emit(f"{tasks_var} = []")

            for selection, _resolver_id in async_fields:
                field_name = self.compiler._sanitize_identifier(selection.name.value)
                alias = (
                    self.compiler._sanitize_identifier(selection.alias.value)
                    if selection.alias
                    else field_name
                )

                # Generate async task with unique name
                task_name = f"task_{field_name}_{gather_id}"
                self.compiler._emit(f"async def {task_name}():")
                self.compiler.indent_level += 1
                self.compiler._emit("temp_result = {}")
                self.generate_field(
                    selection, parent_type, parent_var, "temp_result", info_var, path
                )
                self.compiler._emit(f"return ('{alias}', temp_result.get('{alias}'))")
                self.compiler.indent_level -= 1
                self.compiler._emit(f"{tasks_var}.append({task_name}())")

            self.compiler._emit("")
            self.compiler._emit("# Gather results")
            self.compiler._emit(
                f"{results_var} = await asyncio.gather(*{tasks_var}, return_exceptions=True)"
            )
            self.compiler._emit(f"for {result_item_var} in {results_var}:")
            self.compiler.indent_level += 1
            self.compiler._emit(f"if isinstance({result_item_var}, Exception):")
            self.compiler.indent_level += 1
            self.compiler._emit(
                f"errors.append({{'message': str({result_item_var}), 'path': "
                + path
                + "})"
            )
            self.compiler.indent_level -= 1
            self.compiler._emit(f"elif isinstance({result_item_var}, tuple):")
            self.compiler.indent_level += 1
            self.compiler._emit(f"field_alias, field_value = {result_item_var}")
            self.compiler._emit(f"{result_var}[field_alias] = field_value")
            self.compiler.indent_level -= 1
            self.compiler.indent_level -= 1

        elif async_fields:
            # Single async field - await directly without gather overhead
            for selection, _ in async_fields:
                self.generate_field(
                    selection, parent_type, parent_var, result_var, info_var, path
                )

        # Process fragments
        for selection in fragments:
            if isinstance(selection, FragmentSpreadNode):
                self.generate_fragment_spread(
                    selection, parent_type, parent_var, result_var, info_var, path
                )
            elif isinstance(selection, InlineFragmentNode):
                self.generate_inline_fragment(
                    selection, parent_type, parent_var, result_var, info_var, path
                )

        # Restore depth after processing
        self.compiler.parallel_depth -= 1

    def generate_selection_set(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Generate standard selection set."""
        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                self.generate_field(
                    selection, parent_type, parent_var, result_var, info_var, path
                )
            elif isinstance(selection, FragmentSpreadNode):
                self.generate_fragment_spread(
                    selection, parent_type, parent_var, result_var, info_var, path
                )
            elif isinstance(selection, InlineFragmentNode):
                self.generate_inline_fragment(
                    selection, parent_type, parent_var, result_var, info_var, path
                )

    def generate_field(
        self,
        field: FieldNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Generate optimized field resolution with error handling."""
        field_name = self.compiler._sanitize_identifier(field.name.value)
        alias = (
            self.compiler._sanitize_identifier(field.alias.value)
            if field.alias
            else field_name
        )
        field_path = f"{path} + ['{alias}']"

        # Handle __typename
        if field_name == "__typename":
            safe_type_name = self.compiler._sanitize_identifier(parent_type.name)
            self.compiler._emit(f'{result_var}["{alias}"] = "{safe_type_name}"')
            return

        # Handle introspection fields
        if field_name == "__schema":
            self.compiler._emit("# Introspection: __schema")
            self.compiler._emit("from graphql.type import introspection")
            self.compiler._emit("schema_type = introspection.__Schema")
            self.compiler._emit(f"{result_var}['{alias}'] = {{}}")
            if field.selection_set:
                self.compiler._generate_introspection_selection(
                    field.selection_set,
                    "__Schema",
                    f"{info_var}.schema",
                    f"{result_var}['{alias}']",
                    info_var,
                    field_path,
                )
            return

        if field_name == "__type":
            self.compiler._emit("# Introspection: __type")
            # Get the name argument
            type_name_arg = None
            if field.arguments:
                for arg in field.arguments:
                    if arg.name.value == "name":
                        type_name_arg = self.generate_argument_value(
                            arg.value, info_var
                        )
                        break

            if type_name_arg:
                self.compiler._emit(
                    f"requested_type = {info_var}.schema.get_type({type_name_arg})"
                )
                self.compiler._emit("if requested_type:")
                self.compiler.indent_level += 1
                self.compiler._emit(f"{result_var}['{alias}'] = {{}}")
                if field.selection_set:
                    self.compiler._generate_introspection_selection(
                        field.selection_set,
                        "__Type",
                        "requested_type",
                        f"{result_var}['{alias}']",
                        info_var,
                        field_path,
                    )
                self.compiler.indent_level -= 1
                self.compiler._emit("else:")
                self.compiler.indent_level += 1
                self.compiler._emit(f"{result_var}['{alias}'] = None")
                self.compiler.indent_level -= 1
            else:
                self.compiler._emit(f"{result_var}['{alias}'] = None")
            return

        field_def = parent_type.fields.get(field_name)
        if not field_def:
            return

        # Check if nullable
        is_nullable = not isinstance(field_def.type, GraphQLNonNull)

        # Handle directives
        if field.directives:
            skip_code = self.compiler._generate_skip_include_checks(
                field.directives, info_var
            )
            if skip_code:
                self.compiler._emit(skip_code)
                self.compiler.indent_level += 1

        # Generate field resolution with error handling
        self.compiler._emit("try:")
        self.compiler.indent_level += 1

        # Update info
        self.compiler._emit(f'info.field_name = "{field_name}"')

        # Generate optimized resolver call
        temp_var = f"field_{field_name}_value"

        if field_def.resolve:
            resolver_id = f"resolver_{self.compiler.field_counter}"
            self.compiler.field_counter += 1
            self.compiler.resolver_map[resolver_id] = field_def.resolve

            # Use compile-time async detection from StrawberryField
            if self.is_field_async(field_def):
                self.compiler.async_resolver_ids.add(resolver_id)
                if field.arguments:
                    self.generate_arguments(field, field_def, info_var)
                    self.compiler._emit(
                        f"{temp_var} = await _resolvers['{resolver_id}']({parent_var}, info, **kwargs)"
                    )
                else:
                    self.compiler._emit(
                        f"{temp_var} = await _resolvers['{resolver_id}']({parent_var}, info)"
                    )
            elif field.arguments:
                self.generate_arguments(field, field_def, info_var)
                self.compiler._emit(
                    f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, info, **kwargs)"
                )
            else:
                self.compiler._emit(
                    f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, info)"
                )
        # Inline trivial field access for performance
        elif self.compiler.inline_trivial_resolvers and not field.arguments:
            self.compiler._emit(
                f"{temp_var} = getattr({parent_var}, '{field_name}', None)"
            )
        else:
            self.compiler._emit(f"attr = getattr({parent_var}, '{field_name}', None)")
            if field.arguments:
                self.generate_arguments(field, field_def, info_var)
                self.compiler._emit(
                    f"{temp_var} = attr(**kwargs) if callable(attr) else attr"
                )
            else:
                self.compiler._emit(f"{temp_var} = attr() if callable(attr) else attr")

        # Handle nested selections
        if field.selection_set:
            field_type = field_def.type
            while hasattr(field_type, "of_type"):
                field_type = field_type.of_type

            # Handle Object, Union, and Interface types
            if isinstance(
                field_type, (GraphQLObjectType, GraphQLUnionType, GraphQLInterfaceType)
            ):
                self.compiler._emit(f"if {temp_var} is not None:")
                self.compiler.indent_level += 1

                # Check for list type
                if str(field_def.type).startswith("["):
                    self.compiler._emit(f'{result_var}["{alias}"] = []')
                    # Use unique variable names for nested lists
                    list_counter = self.compiler.nested_counter
                    self.compiler.nested_counter += 1
                    item_var = f"item_{list_counter}"
                    item_result_var = f"item_result_{list_counter}"

                    self.compiler._emit(
                        f"for idx, {item_var} in enumerate({temp_var}):"
                    )
                    self.compiler.indent_level += 1
                    item_path = f"{field_path} + [idx]"

                    # Check if list items can be nullable
                    from graphql import is_non_null_type

                    inner_type = field_def.type
                    # Unwrap non-null wrapper if present
                    if is_non_null_type(inner_type):
                        inner_type = inner_type.of_type
                    # Check if list items are nullable
                    item_type = (
                        inner_type.of_type if hasattr(inner_type, "of_type") else None
                    )
                    items_nullable = item_type and not is_non_null_type(item_type)

                    if items_nullable:
                        # Add null check for nullable list items
                        self.compiler._emit(f"if {item_var} is None:")
                        self.compiler.indent_level += 1
                        self.compiler._emit(f'{result_var}["{alias}"].append(None)')
                        self.compiler.indent_level -= 1
                        self.compiler._emit("else:")
                        self.compiler.indent_level += 1

                    # Wrap item processing in try-except for nullable items
                    if items_nullable:
                        self.compiler._emit("try:")
                        self.compiler.indent_level += 1

                    self.compiler._emit(f"{item_result_var} = {{}}")

                    # For unions/interfaces, we need runtime type resolution
                    if isinstance(field_type, (GraphQLUnionType, GraphQLInterfaceType)):
                        self.compiler._generate_abstract_type_selection(
                            field.selection_set,
                            field_type,
                            item_var,
                            item_result_var,
                            info_var,
                            item_path,
                        )
                    else:
                        # Use parallel execution for list items to match standard GraphQL
                        self.generate_parallel_selection_set(
                            field.selection_set,
                            field_type,
                            item_var,
                            item_result_var,
                            info_var,
                            item_path,
                        )
                    self.compiler._emit(
                        f'{result_var}["{alias}"].append({item_result_var})'
                    )

                    # Add error handling for nullable items
                    if items_nullable:
                        self.compiler.indent_level -= 1
                        self.compiler._emit("except Exception as item_error:")
                        self.compiler.indent_level += 1
                        # Error already added by field-level handler, just append None
                        self.compiler._emit(f'{result_var}["{alias}"].append(None)')
                        self.compiler.indent_level -= 1

                    if items_nullable:
                        self.compiler.indent_level -= 1  # Close the else block
                    self.compiler.indent_level -= 1
                else:
                    # Use a unique variable name for nested results
                    nested_var = f"nested_result_{self.compiler.nested_counter}"
                    self.compiler.nested_counter += 1
                    self.compiler._emit(f"{nested_var} = {{}}")

                    # For unions/interfaces, we need runtime type resolution
                    if isinstance(field_type, (GraphQLUnionType, GraphQLInterfaceType)):
                        self.compiler._generate_abstract_type_selection(
                            field.selection_set,
                            field_type,
                            temp_var,
                            nested_var,
                            info_var,
                            field_path,
                        )
                    else:
                        # Use sequential execution for nested selections to minimize event loop overhead
                        self.generate_selection_set(
                            field.selection_set,
                            field_type,
                            temp_var,
                            nested_var,
                            info_var,
                            field_path,
                        )
                    self.compiler._emit(f'{result_var}["{alias}"] = {nested_var}')

                self.compiler.indent_level -= 1
                self.compiler._emit("else:")
                self.compiler.indent_level += 1
                self.compiler._emit(f'{result_var}["{alias}"] = None')
                self.compiler.indent_level -= 1
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
                self.compiler._emit(f'{result_var}["{alias}"] = {temp_var}')
            elif isinstance(field_type, GraphQLEnumType) or (
                hasattr(field_type, "serialize") and callable(field_type.serialize)
            ):
                # Custom scalar with serialization
                self.compiler._emit(f"# Serialize custom scalar: {field_type.name}")
                if str(field_def.type).startswith("["):
                    # List of scalars
                    self.compiler._emit(f"if {temp_var} is not None:")
                    self.compiler.indent_level += 1
                    self.compiler._emit(f'{result_var}["{alias}"] = []')
                    self.compiler._emit(f"for scalar_item in {temp_var}:")
                    self.compiler.indent_level += 1
                    self.compiler._emit(
                        f"if scalar_item is not None and '{field_type.name}' in _scalar_serializers:"
                    )
                    self.compiler.indent_level += 1
                    self.compiler._emit(
                        f'{result_var}["{alias}"].append(_scalar_serializers["{field_type.name}"](scalar_item))'
                    )
                    self.compiler.indent_level -= 1
                    self.compiler._emit("else:")
                    self.compiler.indent_level += 1
                    self.compiler._emit(f'{result_var}["{alias}"].append(scalar_item)')
                    self.compiler.indent_level -= 1
                    self.compiler.indent_level -= 1
                    self.compiler.indent_level -= 1
                    self.compiler._emit("else:")
                    self.compiler.indent_level += 1
                    self.compiler._emit(f'{result_var}["{alias}"] = None')
                    self.compiler.indent_level -= 1
                else:
                    # Single scalar
                    safe_field_type_name = self.compiler._sanitize_identifier(
                        field_type.name
                    )
                    self.compiler._emit(
                        f"if {temp_var} is not None and '{safe_field_type_name}' in _scalar_serializers:"
                    )
                    self.compiler.indent_level += 1
                    self.compiler._emit(
                        f'{result_var}["{alias}"] = _scalar_serializers["{safe_field_type_name}"]({temp_var})'
                    )
                    self.compiler.indent_level -= 1
                    self.compiler._emit("else:")
                    self.compiler.indent_level += 1
                    self.compiler._emit(f'{result_var}["{alias}"] = {temp_var}')
                    self.compiler.indent_level -= 1
            else:
                # Default - no serialization needed
                self.compiler._emit(f'{result_var}["{alias}"] = {temp_var}')

        # Error handling
        self.compiler.indent_level -= 1
        self.compiler._emit("except Exception as e:")
        self.compiler.indent_level += 1
        # Only add error if no error with this message exists yet
        # This prevents duplicate errors when non-null fields propagate
        self.compiler._emit(
            "if not any(err.get('message') == str(e) for err in errors):"
        )
        self.compiler.indent_level += 1
        # Include field name and type in error for better debugging
        field_type_str = str(field_def.type)
        error_dict = (
            "{"
            f"'message': str(e), "
            f"'path': {field_path}, "
            f"'locations': [], "
            f"'extensions': {{'fieldName': '{field_name}', 'fieldType': '{field_type_str}', 'alias': '{alias}'}}"
            "}"
        )
        self.compiler._emit(f"errors.append({error_dict})")
        self.compiler.indent_level -= 1

        if is_nullable:
            # For nullable fields, set to null and don't propagate
            self.compiler._emit(f'{result_var}["{alias}"] = None')
        else:
            # For non-null fields, propagate the exception
            # Error was already added at the deepest level
            self.compiler._emit("raise  # Propagate non-nullable error")
        self.compiler.indent_level -= 1

        # Close directive block
        if field.directives and skip_code:
            self.compiler.indent_level -= 1

    def generate_arguments(
        self, field: FieldNode, field_def: GraphQLField, info_var: str
    ) -> None:
        """Generate field arguments handling."""
        self.compiler._emit("kwargs = {}")

        # Add defaults
        if field_def.args:
            for arg_name, arg_def in field_def.args.items():
                if (
                    hasattr(arg_def, "default_value")
                    and arg_def.default_value is not Undefined
                ):
                    default_val = self.compiler._serialize_value(arg_def.default_value)
                    self.compiler._emit(f"kwargs['{arg_name}'] = {default_val}")

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
                arg_code = self.generate_argument_value(arg.value, info_var, arg_type)
                self.compiler._emit(f"kwargs['{arg_name}'] = {arg_code}")

    def generate_argument_value(
        self, value_node: ValueNode, info_var: str, arg_type: GraphQLType | None = None
    ) -> str:
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
            var_name = self.compiler._sanitize_identifier(value_node.name.value)
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
                        # Apply parse_value to each element in the list, preserving None
                        safe_type_name = self.compiler._sanitize_identifier(
                            item_type.name
                        )
                        parser_func = (
                            f"_scalar_parsers.get('{safe_type_name}', lambda x: x)"
                        )
                        return f"([{parser_func}(item) if item is not None else None for item in {var_code}] if {var_code} is not None else None)"
                else:
                    # Single value - check if it's a custom scalar
                    scalar_type = arg_type
                    while hasattr(scalar_type, "of_type"):
                        scalar_type = scalar_type.of_type

                    if hasattr(scalar_type, "name") and hasattr(
                        scalar_type, "parse_value"
                    ):
                        # This is a custom scalar - wrap with parse_value
                        safe_type_name = self.compiler._sanitize_identifier(
                            scalar_type.name
                        )
                        return f"(_scalar_parsers.get('{safe_type_name}', lambda x: x)({var_code}) if {var_code} is not None else None)"

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
                    safe_type_name = self.compiler._sanitize_identifier(
                        scalar_type.name
                    )
                    return f"_scalar_parsers.get('{safe_type_name}', lambda x: x)({value_node.value!r})"

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
                        safe_type_name = self.compiler._sanitize_identifier(
                            enum_type.name
                        )
                        safe_enum_value = self.compiler._sanitize_identifier(
                            enum_value_name
                        )
                        return f"_schema.type_map['{safe_type_name}'].values['{safe_enum_value}'].value"

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
                self.generate_argument_value(item, info_var, item_type)
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
                val = self.generate_argument_value(field.value, info_var, field_type)
                items.append(f"{key}: {val}")
            return f"{{{', '.join(items)}}}"
        return "None"

    def generate_fragment_spread(
        self,
        fragment_spread: FragmentSpreadNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Generate fragment spread."""
        fragment_name = fragment_spread.name.value
        if fragment_name not in self.compiler.fragments:
            raise ValueError(f"Fragment '{fragment_name}' not found")

        fragment_def = self.compiler.fragments[fragment_name]
        type_condition = fragment_def.type_condition.name.value

        if parent_type.name == type_condition:
            if fragment_def.selection_set:
                self.generate_selection_set(
                    fragment_def.selection_set,
                    parent_type,
                    parent_var,
                    result_var,
                    info_var,
                    path,
                )
        else:
            self.compiler._emit(f"# Fragment spread: {fragment_name}")
            self.compiler._emit(
                f"if hasattr({parent_var}, '__typename') and {parent_var}.__typename == '{type_condition}':"
            )
            self.compiler.indent_level += 1
            if fragment_def.selection_set:
                self.generate_selection_set(
                    fragment_def.selection_set,
                    parent_type,
                    parent_var,
                    result_var,
                    info_var,
                    path,
                )
            self.compiler.indent_level -= 1

    def generate_inline_fragment(
        self,
        inline_fragment: InlineFragmentNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Generate inline fragment."""
        if inline_fragment.type_condition:
            type_name = inline_fragment.type_condition.name.value
            fragment_type = self.compiler.schema.type_map.get(type_name)

            if not fragment_type or not isinstance(fragment_type, GraphQLObjectType):
                return

            if type_name == parent_type.name:
                if inline_fragment.selection_set:
                    self.generate_selection_set(
                        inline_fragment.selection_set,
                        fragment_type,
                        parent_var,
                        result_var,
                        info_var,
                        path,
                    )
            else:
                self.compiler._emit(f"# Inline fragment on {type_name}")
                self.compiler._emit(
                    f"if hasattr({parent_var}, '__typename') and {parent_var}.__typename == '{type_name}':"
                )
                self.compiler.indent_level += 1
                if inline_fragment.selection_set:
                    self.generate_selection_set(
                        inline_fragment.selection_set,
                        fragment_type,
                        parent_var,
                        result_var,
                        info_var,
                        path,
                    )
                self.compiler.indent_level -= 1
        elif inline_fragment.selection_set:
            self.generate_selection_set(
                inline_fragment.selection_set,
                parent_type,
                parent_var,
                result_var,
                info_var,
                path,
            )
