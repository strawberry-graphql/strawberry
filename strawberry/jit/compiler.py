"""Unified JIT compiler for Strawberry GraphQL.

This module provides the production-ready JIT compiler that combines:
- Aggressive compile-time optimizations
- Parallel async execution with asyncio.gather()
- GraphQL spec-compliant error handling
- Support for fragments, directives, and arguments
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from graphql import (
    DirectiveNode,
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLType,
    GraphQLUnionType,
    InlineFragmentNode,
    SelectionSetNode,
    execute_sync,
    get_operation_root_type,
    parse,
    validate,
)
from graphql.language import OperationDefinitionNode, ValueNode

if TYPE_CHECKING:
    from collections.abc import Callable

    import strawberry
else:
    import strawberry  # noqa: TC001

from .codegen import CodeGenerator
from .directives import (
    generate_abstract_type_selection,
    generate_skip_include_checks,
    get_directive_argument,
)
from .introspection import generate_introspection_selection
from .types import MockInfo
from .utils import detect_async_resolvers, sanitize_identifier, serialize_value


class JITCompiler:
    """Unified high-performance JIT compiler for GraphQL queries.

    Features:
    - Compile-time optimizations for maximum performance
    - Parallel async execution for independent fields
    - Full GraphQL spec compliance including error handling
    - Built-in caching with configurable TTL and size limits
    """

    def __init__(self, schema: strawberry.Schema) -> None:
        """Initialize JIT compiler with a Strawberry schema.

        Args:
            schema: A Strawberry schema instance
        """
        if not hasattr(schema, "_schema"):
            raise TypeError(
                "JIT compiler requires a Strawberry schema. "
                "Create one with strawberry.Schema(Query)"
            )

        self.strawberry_schema = schema
        self.schema = schema._schema  # GraphQL Core schema for AST operations
        self.type_map = schema.type_map  # Native Strawberry type map
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

    def _sanitize_identifier(self, name: str) -> str:
        """Sanitize identifier for safe code generation (defense-in-depth).

        While GraphQL parser validates identifiers, this provides an additional
        security layer to prevent any potential code injection through names
        embedded in generated code.

        Args:
            name: Identifier to sanitize (field name, alias, variable name, etc.)

        Returns:
            The validated identifier

        Raises:
            ValueError: If identifier is invalid
        """
        return sanitize_identifier(name)

    def _serialize_value(self, value: Any) -> str:
        """Serialize Python value for code generation."""
        return serialize_value(value)

    def compile_query(self, query: str) -> Callable:
        """Compile a GraphQL query into optimized Python code."""
        document = parse(query)

        # Check for @defer/@stream directives BEFORE validation
        # (GraphQL validation will fail on unknown directives)
        if self._has_defer_or_stream(document):
            warnings.warn(
                "Query contains @defer or @stream directives which are not "
                "supported by the JIT compiler. Falling back to standard GraphQL "
                "executor. Performance will be the same as non-JIT execution.",
                UserWarning,
                stacklevel=2,
            )

            # Return a wrapper that calls standard GraphQL executor
            def fallback_executor(
                root_value: Any = None,
                variables: dict[str, Any] | None = None,
                context_value: Any = None,
                operation_name: str | None = None,
            ) -> dict[str, Any]:
                """Fallback to standard GraphQL executor for @defer/@stream."""
                result = execute_sync(
                    self.schema,
                    document,
                    root_value=root_value,
                    variable_values=variables,
                    context_value=context_value,
                    operation_name=operation_name,
                )

                # Convert to JIT-compatible format
                return {
                    "data": result.data,
                    "errors": [
                        {
                            "message": str(e.message),
                            "locations": [
                                {"line": loc.line, "column": loc.column}
                                for loc in (e.locations or [])
                            ],
                            "path": list(e.path) if e.path else None,
                        }
                        for e in (result.errors or [])
                    ]
                    if result.errors
                    else [],
                }

            return fallback_executor

        # Validate query (only for non-defer/stream queries)
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

        # Generate optimized function code using CodeGenerator
        code_generator = CodeGenerator(self)
        function_code = code_generator.generate_optimized_function(operation, root_type)

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
        exec(compiled_code, local_vars)  # noqa: S102

        # Store the source code on the function for debugging/inspection
        execute_fn = local_vars["execute_query"]
        execute_fn._jit_source = function_code

        return execute_fn

    def _reset_state(self) -> None:
        """Reset compiler state for new compilation."""
        self.generated_code = []
        self.indent_level = 0
        self.field_counter = 0
        self.resolver_map = {}
        self.has_async_resolvers = False
        self.async_resolver_ids = set()
        self.nested_counter = 0

    def _get_operation(self, document: DocumentNode) -> OperationDefinitionNode | None:
        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                return definition
        return None

    def _extract_fragments(self, document: DocumentNode) -> None:
        """Extract fragment definitions from document."""
        self.fragments = {}
        for definition in document.definitions:
            if isinstance(definition, FragmentDefinitionNode):
                self.fragments[definition.name.value] = definition

    def _is_field_async(self, field_def: GraphQLField) -> bool:
        """Wrapper to check if a field is async - delegates to CodeGenerator."""
        code_generator = CodeGenerator(self)
        return code_generator.is_field_async(field_def)

    def _generate_parallel_selection_set(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Delegate to CodeGenerator."""
        code_generator = CodeGenerator(self)
        return code_generator.generate_parallel_selection_set(
            selection_set, parent_type, parent_var, result_var, info_var, path
        )

    def _generate_selection_set(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Delegate to CodeGenerator."""
        code_generator = CodeGenerator(self)
        return code_generator.generate_selection_set(
            selection_set, parent_type, parent_var, result_var, info_var, path
        )

    def _generate_field(
        self,
        field: FieldNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Delegate to CodeGenerator."""
        code_generator = CodeGenerator(self)
        return code_generator.generate_field(
            field, parent_type, parent_var, result_var, info_var, path
        )

    def _generate_arguments(
        self, field: FieldNode, field_def: GraphQLField, info_var: str
    ) -> None:
        """Delegate to CodeGenerator."""
        code_generator = CodeGenerator(self)
        return code_generator.generate_arguments(field, field_def, info_var)

    def _generate_argument_value(
        self, value_node: ValueNode, info_var: str, arg_type: GraphQLType | None = None
    ) -> str:
        """Delegate to CodeGenerator."""
        code_generator = CodeGenerator(self)
        return code_generator.generate_argument_value(value_node, info_var, arg_type)

    def _generate_fragment_spread(
        self,
        fragment_spread: FragmentSpreadNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Delegate to CodeGenerator."""
        code_generator = CodeGenerator(self)
        return code_generator.generate_fragment_spread(
            fragment_spread, parent_type, parent_var, result_var, info_var, path
        )

    def _generate_inline_fragment(
        self,
        inline_fragment: InlineFragmentNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Delegate to CodeGenerator."""
        code_generator = CodeGenerator(self)
        return code_generator.generate_inline_fragment(
            inline_fragment, parent_type, parent_var, result_var, info_var, path
        )

    def _generate_introspection_selection(
        self,
        selection_set: SelectionSetNode,
        introspection_type: str,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Generate selection for introspection types (__Schema, __Type, etc)."""
        return generate_introspection_selection(
            self,
            selection_set,
            introspection_type,
            parent_var,
            result_var,
            info_var,
            path,
        )

    def _generate_abstract_type_selection(
        self,
        selection_set: SelectionSetNode,
        abstract_type: GraphQLUnionType | GraphQLInterfaceType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str,
    ) -> None:
        """Generate selection for union or interface types with runtime type resolution."""
        return generate_abstract_type_selection(
            self, selection_set, abstract_type, parent_var, result_var, info_var, path
        )

    def _generate_skip_include_checks(
        self, directives: list[DirectiveNode], info_var: str
    ) -> str:
        """Generate directive conditions."""
        return generate_skip_include_checks(self, directives, info_var)

    def _get_directive_argument(
        self, directive: DirectiveNode, arg_name: str, info_var: str
    ) -> str:
        """Get directive argument value."""
        return get_directive_argument(self, directive, arg_name, info_var)

    def _is_field_async(self, field_def: GraphQLField) -> bool:
        """Check if field is async - delegate to CodeGenerator."""
        code_generator = CodeGenerator(self)
        return code_generator.is_field_async(field_def)

    def _detect_async_resolvers(
        self, selection_set: SelectionSetNode, parent_type: GraphQLObjectType
    ) -> None:
        """Pre-scan for async resolvers."""
        has_async = detect_async_resolvers(
            selection_set,
            parent_type,
            self.fragments,
            self.schema,
            self._is_field_async,
        )
        if has_async:
            self.has_async_resolvers = True

    def _emit(self, line: str) -> None:
        """Emit line of code with proper indentation."""
        indent = "    " * self.indent_level
        self.generated_code.append(f"{indent}{line}")

    def _has_defer_or_stream(self, document: DocumentNode) -> bool:
        """Check if document contains @defer or @stream directives.

        These directives require incremental response delivery which is not
        supported by the JIT compiler. Queries containing them will fall back
        to the standard GraphQL executor.

        Args:
            document: The parsed GraphQL document

        Returns:
            True if @defer or @stream directives are found
        """

        def check_directives(directives: list[DirectiveNode] | None) -> bool:
            """Check if any directive is defer or stream."""
            if not directives:
                return False
            return any(d.name.value in ("defer", "stream") for d in directives)

        def check_selection_set(selection_set: SelectionSetNode | None) -> bool:
            """Recursively check selection set for defer/stream directives."""
            if not selection_set:
                return False

            for selection in selection_set.selections:
                # Check directives on fields
                if isinstance(selection, FieldNode):
                    if check_directives(selection.directives):
                        return True
                    # Recurse into nested selections
                    if check_selection_set(selection.selection_set):
                        return True

                # Check directives on fragment spreads
                elif isinstance(selection, FragmentSpreadNode):
                    if check_directives(selection.directives):
                        return True

                # Check directives on inline fragments
                elif isinstance(selection, InlineFragmentNode):
                    if check_directives(selection.directives):
                        return True
                    # Recurse into inline fragment selections
                    if check_selection_set(selection.selection_set):
                        return True

            return False

        # Check all operations and fragments in the document
        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                if check_directives(definition.directives):
                    return True
                if check_selection_set(definition.selection_set):
                    return True
            elif isinstance(definition, FragmentDefinitionNode):
                if check_directives(definition.directives):
                    return True
                if check_selection_set(definition.selection_set):
                    return True

        return False


# Public API
def compile_query(schema: strawberry.Schema, query: str) -> Callable:
    """Compile a GraphQL query into optimized Python code.

    This is the main entry point for JIT compilation.

    Args:
        schema: A Strawberry schema instance
        query: The GraphQL query string

    Returns:
        A compiled function that executes the query
    """
    compiler = JITCompiler(schema)
    return compiler.compile_query(query)


__all__ = ["JITCompiler", "compile_query"]
