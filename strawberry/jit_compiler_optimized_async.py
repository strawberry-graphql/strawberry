"""JIT compiler with compile-time async detection.

This version eliminates runtime `inspect.iscoroutinefunction()` calls by
detecting async fields at compile time and generating optimized code.
"""

from __future__ import annotations

import inspect
from typing import Callable, Dict, Set

from graphql import (
    FieldNode,
    FragmentSpreadNode,
    GraphQLObjectType,
    GraphQLSchema,
    InlineFragmentNode,
    SelectionSetNode,
)

from strawberry.jit_compiler import GraphQLJITCompiler


def analyze_schema_async_fields(schema: GraphQLSchema) -> Dict[str, Set[str]]:
    """Analyze a GraphQL schema to determine which fields are async.
    Returns a mapping of type_name -> set of async field names.

    This function is called once at compile time to avoid runtime checks.
    """
    async_fields = {}

    for type_name, type_def in schema.type_map.items():
        if isinstance(type_def, GraphQLObjectType):
            async_field_names = set()

            for field_name, field_def in type_def.fields.items():
                # Check if the field has a custom resolver
                if field_def.resolve:
                    if inspect.iscoroutinefunction(field_def.resolve):
                        async_field_names.add(field_name)

            if async_field_names:
                async_fields[type_name] = async_field_names

    return async_fields


class OptimizedAsyncJITCompiler(GraphQLJITCompiler):
    """JIT compiler with compile-time async detection.

    This compiler pre-analyzes the schema to identify async fields,
    eliminating the need for runtime `inspect.iscoroutinefunction()` checks.
    """

    def __init__(self, schema: GraphQLSchema):
        super().__init__(schema)
        # Pre-analyze the schema for async fields
        self.async_fields_map = analyze_schema_async_fields(schema)
        # Track which fields we know are async at compile time
        self.known_async_fields = set()
        self.known_sync_fields = set()

    def _is_field_async(self, type_name: str, field_name: str) -> bool:
        """Check if a field is async based on compile-time analysis."""
        return (
            type_name in self.async_fields_map
            and field_name in self.async_fields_map[type_name]
        )

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
                    # Use compile-time knowledge instead of runtime check
                    if self._is_field_async(parent_type.name, field_name):
                        self.has_async_resolvers = True
                        self.known_async_fields.add((parent_type.name, field_name))
                    else:
                        self.known_sync_fields.add((parent_type.name, field_name))

                    # Also check if the default field access might be async
                    # For fields without custom resolvers, we still need runtime checks
                    # unless we have metadata from Strawberry's field definitions
                    if not field_def.resolve:
                        # We can't know at compile time if the attribute/method is async
                        # without Strawberry metadata, so be conservative
                        pass

                    # Recurse into nested selections
                    if selection.selection_set:
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

    def _generate_field(
        self,
        field: FieldNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
    ):
        """Generate field resolution with compile-time async knowledge."""
        field_name = field.name.value
        alias = field.alias.value if field.alias else field_name

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

        # Check if we know at compile time whether this field is async
        is_known_async = (parent_type.name, field_name) in self.known_async_fields
        is_known_sync = (parent_type.name, field_name) in self.known_sync_fields

        # Get the resolver function from the field definition
        if field_def.resolve:
            self.resolver_map[resolver_id] = field_def.resolve
            # We already know if it's async from our compile-time analysis
            if is_known_async:
                self.async_resolver_ids.add(resolver_id)
        else:
            # Use a default resolver that gets the attribute
            self.resolver_map[resolver_id] = None

        # Generate code to call the resolver
        temp_var = f"field_{field_name}_value"

        # Update info object for this field
        self._emit(f'{info_var}.field_name = "{field_name}"')
        self._emit(f'{info_var}.parent_type = "{parent_type.name}"')

        # Handle field arguments if any
        if field.arguments or (field_def.args and len(field_def.args) > 0):
            # Build arguments dictionary including defaults
            self._emit("kwargs = {}")

            # First, handle default values from schema
            if field_def.args:
                for arg_name, arg_def in field_def.args.items():
                    if hasattr(arg_def, "default_value"):
                        # Skip Undefined sentinel values
                        from graphql import Undefined

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

            # Use compile-time knowledge to generate exact code
            if is_known_async:
                self._emit(f"# Field '{field_name}' is async (known at compile time)")
                if field.arguments or (field_def.args and len(field_def.args) > 0):
                    self._emit(
                        f"{temp_var} = await resolver({parent_var}, {info_var}, **kwargs)"
                    )
                else:
                    self._emit(f"{temp_var} = await resolver({parent_var}, {info_var})")
            elif is_known_sync:
                self._emit(f"# Field '{field_name}' is sync (known at compile time)")
                if field.arguments or (field_def.args and len(field_def.args) > 0):
                    self._emit(
                        f"{temp_var} = resolver({parent_var}, {info_var}, **kwargs)"
                    )
                else:
                    self._emit(f"{temp_var} = resolver({parent_var}, {info_var})")
            # Fallback to runtime check if we don't have compile-time knowledge
            # This shouldn't happen with custom resolvers, but keep for safety
            elif resolver_id in self.async_resolver_ids:
                if field.arguments or (field_def.args and len(field_def.args) > 0):
                    self._emit(
                        f"{temp_var} = await resolver({parent_var}, {info_var}, **kwargs)"
                    )
                else:
                    self._emit(
                        f"{temp_var} = await resolver({parent_var}, {info_var})"
                    )
            elif field.arguments or (field_def.args and len(field_def.args) > 0):
                self._emit(
                    f"{temp_var} = resolver({parent_var}, {info_var}, **kwargs)"
                )
            else:
                self._emit(f"{temp_var} = resolver({parent_var}, {info_var})")
        # Use default field resolution
        elif field.arguments or (field_def.args and len(field_def.args) > 0):
            self._emit(f"attr = getattr({parent_var}, '{field_name}', None)")
            self._emit("if callable(attr):")
            self.indent_level += 1

            # For fields without custom resolvers, we still need runtime checks
            # unless we have Strawberry metadata
            if self.has_async_resolvers:
                self._emit(
                    "# Runtime check needed - no compile-time info for default resolver"
                )
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

        # Continue with nested field resolution...
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

        # Close directive conditional block if needed
        if field.directives and self._generate_skip_include_checks(
            field.directives, info_var
        ):
            self.indent_level -= 1


def compile_query_optimized(schema: GraphQLSchema, query: str) -> Callable:
    """Compile a GraphQL query with optimized async detection."""
    compiler = OptimizedAsyncJITCompiler(schema)
    return compiler.compile_query(query)
