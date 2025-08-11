"""JIT compiler with parallel async execution using asyncio.gather().

This version executes independent async fields in parallel for better performance.
"""

from __future__ import annotations

import inspect
import textwrap
from typing import Callable, Dict, List, Tuple

from graphql import (
    FieldNode,
    FragmentSpreadNode,
    GraphQLObjectType,
    GraphQLSchema,
    InlineFragmentNode,
    SelectionSetNode,
)
from graphql.language import OperationDefinitionNode

from strawberry.jit_compiler import GraphQLJITCompiler


class ParallelAsyncJITCompiler(GraphQLJITCompiler):
    """JIT compiler with parallel async execution.

    This compiler generates code that uses asyncio.gather() to execute
    independent async fields in parallel, significantly improving performance
    for queries with multiple async fields at the same level.
    """

    def __init__(self, schema: GraphQLSchema):
        super().__init__(schema)
        self.parallel_execution_enabled = True
        # Track async fields at each level for parallel execution
        self.async_fields_by_level: Dict[int, List[Tuple[str, str]]] = {}
        self.current_level = 0

    def _generate_function(
        self, operation: OperationDefinitionNode, root_type: GraphQLObjectType
    ) -> str:
        """Generate function with parallel async support."""
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
Standalone JIT-compiled GraphQL executor with parallel async execution.
This file was automatically generated and can be executed independently.

Query Details:
- Operation: {operation_type} {operation_name}
- Root Type: {root_type_name}
- Top-level Fields: {fields}
- Generated: [timestamp]
- Features: Parallel async execution with asyncio.gather()
"""

from typing import Any, Dict, List, Optional'''

        header = header_template.format(
            operation_type=operation_type,
            operation_name=operation_name,
            root_type_name=root_type.name,
            fields=", ".join(fields_selected) if fields_selected else "none",
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
        self._emit(
            '"""Execute the JIT-compiled GraphQL query with parallel async execution."""'
        )
        self._emit("result = {}")
        self._emit("info = _MockInfo(None)  # Mock info object")
        self._emit("info.root_value = root")
        self._emit("info.context = context")
        self._emit("info.variable_values = variables or {}")

        if operation.selection_set:
            # Generate selection set with parallel execution
            self._generate_selection_set_parallel(
                operation.selection_set, root_type, "root", "result", "info", path="[]"
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
                self._emit(
                    f"_resolvers['{resolver_id}'] = _default_resolver  # Custom resolver in actual execution"
                )

        # Add main block for standalone execution
        self.generated_code.append("")
        self.generated_code.append("")
        self._emit("if __name__ == '__main__':")
        self.indent_level += 1
        self._emit("# Example usage when run standalone")
        self._emit(
            "print('This is a JIT-compiled GraphQL executor with parallel async execution.')"
        )
        self._emit(
            "print('To use it, import and call execute_query() with your root object.')"
        )

        code = "\n".join(self.generated_code)
        return code

    def _generate_selection_set_parallel(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        info_var: str,
        path: str = "[]",
    ):
        """Generate selection set with parallel execution for async fields.

        This method groups async fields together and executes them in parallel
        using asyncio.gather(), while sync fields are executed sequentially.
        """
        # Separate sync and async field selections
        sync_selections = []
        async_selections = []
        fragment_selections = []

        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                if field_name == "__typename":
                    sync_selections.append(selection)
                    continue

                field_def = parent_type.fields.get(field_name)
                if field_def:
                    # Check if field is async
                    is_async = False
                    if field_def.resolve and inspect.iscoroutinefunction(
                        field_def.resolve
                    ):
                        is_async = True

                    if is_async:
                        async_selections.append(selection)
                    else:
                        sync_selections.append(selection)
                else:
                    sync_selections.append(selection)
            elif isinstance(selection, (FragmentSpreadNode, InlineFragmentNode)):
                fragment_selections.append(selection)

        # Process sync fields first
        for selection in sync_selections:
            self._generate_field(
                selection, parent_type, parent_var, result_var, info_var
            )

        # Process async fields in parallel if there are multiple
        if len(async_selections) > 1 and self.has_async_resolvers:
            self._emit("# Execute async fields in parallel")
            self._emit("async_tasks = []")

            # Generate async field tasks
            for i, selection in enumerate(async_selections):
                field_name = selection.name.value
                alias = selection.alias.value if selection.alias else field_name

                # Create a unique function name for each async field
                func_name = f"_resolve_{field_name}_{i}"

                # Generate async function for this field
                self._emit(f"async def {func_name}():")
                self.indent_level += 1

                # Generate field resolution code
                temp_result = f"field_result_{i}"
                self._emit(f"{temp_result} = {{}}")
                self._generate_field(
                    selection, parent_type, parent_var, temp_result, info_var
                )
                self._emit(f"return ('{alias}', {temp_result}.get('{alias}'))")

                self.indent_level -= 1
                self._emit(f"async_tasks.append({func_name}())")

            # Execute all async tasks in parallel
            self._emit("")
            self._emit("# Wait for all async fields to complete")
            self._emit("async_results = await asyncio.gather(*async_tasks)")
            self._emit("for field_alias, field_value in async_results:")
            self.indent_level += 1
            self._emit(f"{result_var}[field_alias] = field_value")
            self.indent_level -= 1
        elif async_selections:
            # Process single async field or when not async
            for selection in async_selections:
                self._generate_field(
                    selection, parent_type, parent_var, result_var, info_var, path
                )

        # Process fragments
        for selection in fragment_selections:
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
        path: str = "[]",
    ):
        """Override to use parallel execution when beneficial.

        This method delegates to the parallel version when async fields are present
        and parallel execution is enabled.
        """
        if self.parallel_execution_enabled and self.has_async_resolvers:
            # Use parallel execution for async fields
            self._generate_selection_set_parallel(
                selection_set, parent_type, parent_var, result_var, info_var, path
            )
        else:
            # Fall back to sequential execution
            super()._generate_selection_set(
                selection_set, parent_type, parent_var, result_var, info_var, path
            )


def compile_query_parallel(schema: GraphQLSchema, query: str) -> Callable:
    """Compile a GraphQL query with parallel async execution."""
    compiler = ParallelAsyncJITCompiler(schema)
    return compiler.compile_query(query)
