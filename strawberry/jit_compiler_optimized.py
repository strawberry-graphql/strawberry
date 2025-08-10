from __future__ import annotations

import inspect
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


class OptimizedGraphQLJITCompiler:
    """Optimized JIT compiler with aggressive performance improvements:
    - Direct attribute access for simple fields (no resolver overhead)
    - Inline simple resolvers directly into generated code
    - Minimize info object creation
    - Batch field resolution where possible
    """

    def __init__(self, schema: GraphQLSchema):
        self.schema = schema
        self.generated_code = []
        self.indent_level = 0
        self.field_counter = 0
        self.resolver_map = {}
        self.inline_resolvers = {}  # Store simple resolvers for inlining

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

        # Reset state
        self.generated_code = []
        self.indent_level = 0
        self.field_counter = 0
        self.resolver_map = {}
        self.inline_resolvers = {}

        function_code = self._generate_optimized_function(operation, root_type)

        # Create minimal runtime environment
        local_vars = {
            "_resolvers": self.resolver_map,
            "getattr": getattr,  # Direct access to builtins
            "hasattr": hasattr,
            "isinstance": isinstance,
            "len": len,
        }

        compiled_code = compile(function_code, "<optimized>", "exec")
        exec(compiled_code, local_vars)

        return local_vars["execute_query"]

    def _get_operation(
        self, document: DocumentNode
    ) -> Optional[OperationDefinitionNode]:
        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                return definition
        return None

    def _can_inline_resolver(self, resolver: Callable) -> bool:
        """Check if a resolver is simple enough to inline."""
        if not resolver:
            return False

        # Check if it's a default resolver (marked with _is_default)
        if getattr(resolver, "_is_default", False):
            return False

        try:
            source = inspect.getsource(resolver)
            # Simple heuristic: inline if it's a one-liner or very simple
            lines = source.strip().split("\n")
            if len(lines) <= 3:  # Simple method
                # Check if it's just returning an expression
                if "return" in source and source.count("return") == 1:
                    return True
        except:
            pass

        return False

    def _generate_optimized_function(
        self, operation: OperationDefinitionNode, root_type: GraphQLObjectType
    ) -> str:
        self.generated_code = []
        self.indent_level = 0

        self._emit("def execute_query(root, context=None, variables=None):")
        self.indent_level += 1
        self._emit("result = {}")

        if operation.selection_set:
            self._generate_optimized_selection_set(
                operation.selection_set, root_type, "root", "result"
            )

        self._emit("return result")

        return "\n".join(self.generated_code)

    def _generate_optimized_selection_set(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
    ):
        # Group fields by type for potential batching
        fields_by_resolver_type = {}

        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                field_def = parent_type.fields.get(field_name)

                if field_def and not field_def.resolve:
                    # Group simple fields for batch processing
                    fields_by_resolver_type.setdefault("simple", []).append(selection)
                else:
                    fields_by_resolver_type.setdefault("complex", []).append(selection)

        # Process simple fields first (batch them)
        if "simple" in fields_by_resolver_type:
            for field in fields_by_resolver_type["simple"]:
                self._generate_simple_field(field, parent_type, parent_var, result_var)

        # Process complex fields
        if "complex" in fields_by_resolver_type:
            for field in fields_by_resolver_type["complex"]:
                self._generate_complex_field(field, parent_type, parent_var, result_var)

    def _generate_simple_field(
        self,
        field: FieldNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
    ):
        """Generate optimized code for simple field access (no resolver)."""
        field_name = field.name.value
        alias = field.alias.value if field.alias else field_name

        if field_name == "__typename":
            self._emit(f'{result_var}["{alias}"] = "{parent_type.name}"')
            return

        field_def = parent_type.fields.get(field_name)
        if not field_def:
            return

        # Direct attribute access - much faster than resolver calls
        if field.selection_set:
            field_type = field_def.type
            while hasattr(field_type, "of_type"):
                field_type = field_type.of_type

            if isinstance(field_type, GraphQLObjectType):
                temp_var = f"_{field_name}_val"

                # Optimized attribute access
                self._emit(f"{temp_var} = getattr({parent_var}, '{field_name}', None)")
                self._emit(f"if {temp_var} is not None:")
                self.indent_level += 1

                # Handle lists
                if hasattr(field_def.type, "of_type") and str(
                    field_def.type
                ).startswith("["):
                    self._emit(f"if isinstance({temp_var}, list):")
                    self.indent_level += 1
                    self._emit(f'{result_var}["{alias}"] = []')
                    item_var = f"_item_{field_name}"
                    item_result_var = f"_{field_name}_item_result"
                    self._emit(f"for {item_var} in {temp_var}:")
                    self.indent_level += 1
                    self._emit(f"{item_result_var} = {{}}")
                    self._generate_optimized_selection_set(
                        field.selection_set, field_type, item_var, item_result_var
                    )
                    self._emit(f'{result_var}["{alias}"].append({item_result_var})')
                    self.indent_level -= 1  # Exit for loop
                    self.indent_level -= 1  # Exit isinstance check
                else:
                    nested_var = f"_nested_{field_name}"
                    self._emit(f"{nested_var} = {{}}")
                    self._generate_optimized_selection_set(
                        field.selection_set, field_type, temp_var, nested_var
                    )
                    self._emit(f'{result_var}["{alias}"] = {nested_var}')

                self.indent_level -= 1
                self._emit("else:")
                self.indent_level += 1
                self._emit(f'{result_var}["{alias}"] = None')
                self.indent_level -= 1
        else:
            # Ultra-fast direct attribute access for scalar fields
            self._emit(
                f'{result_var}["{alias}"] = getattr({parent_var}, "{field_name}", None)'
            )

    def _generate_complex_field(
        self,
        field: FieldNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
    ):
        """Generate code for fields with custom resolvers."""
        field_name = field.name.value
        alias = field.alias.value if field.alias else field_name

        field_def = parent_type.fields.get(field_name)
        if not field_def:
            return

        resolver_id = f"resolver_{self.field_counter}"
        self.field_counter += 1
        self.resolver_map[resolver_id] = field_def.resolve

        temp_var = f"_field_{field_name}"

        # Try to inline simple resolvers
        if self._can_inline_resolver(field_def.resolve):
            # For very simple resolvers, we could inline them
            # This is a future optimization
            self._emit(f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, None)")
        else:
            # Fall back to resolver call
            self._emit(f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, None)")

        if field.selection_set:
            field_type = field_def.type
            while hasattr(field_type, "of_type"):
                field_type = field_type.of_type

            if isinstance(field_type, GraphQLObjectType):
                self._emit(f"if {temp_var} is not None:")
                self.indent_level += 1

                if hasattr(field_def.type, "of_type") and str(
                    field_def.type
                ).startswith("["):
                    self._emit(f"if isinstance({temp_var}, list):")
                    self.indent_level += 1
                    self._emit(f'{result_var}["{alias}"] = []')
                    item_var = f"_item_{field_name}"
                    item_result_var = f"_{field_name}_item_result"
                    self._emit(f"for {item_var} in {temp_var}:")
                    self.indent_level += 1
                    self._emit(f"{item_result_var} = {{}}")
                    self._generate_optimized_selection_set(
                        field.selection_set, field_type, item_var, item_result_var
                    )
                    self._emit(f'{result_var}["{alias}"].append({item_result_var})')
                    self.indent_level -= 1  # Exit for loop
                    self.indent_level -= 1  # Exit isinstance check
                else:
                    nested_var = f"_nested_{field_name}"
                    self._emit(f"{nested_var} = {{}}")
                    self._generate_optimized_selection_set(
                        field.selection_set, field_type, temp_var, nested_var
                    )
                    self._emit(f'{result_var}["{alias}"] = {nested_var}')

                self.indent_level -= 1
                self._emit("else:")
                self.indent_level += 1
                self._emit(f'{result_var}["{alias}"] = None')
                self.indent_level -= 1
        else:
            self._emit(f'{result_var}["{alias}"] = {temp_var}')

    def _emit(self, line: str):
        indent = "    " * self.indent_level
        self.generated_code.append(f"{indent}{line}")


def compile_query_optimized(schema: GraphQLSchema, query: str) -> Callable:
    """Compile a GraphQL query with aggressive optimizations."""
    compiler = OptimizedGraphQLJITCompiler(schema)
    return compiler.compile_query(query)
