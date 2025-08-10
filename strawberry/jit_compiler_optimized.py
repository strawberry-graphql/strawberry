from __future__ import annotations

import inspect
from typing import Callable, Optional

from graphql import (
    DocumentNode,
    FieldNode,
    GraphQLObjectType,
    GraphQLSchema,
    SelectionSetNode,
    Undefined,
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

        # Handle field arguments for simple fields (methods)
        if field.arguments or (field_def.args and len(field_def.args) > 0):
            # Build arguments dictionary inline for optimization
            args_code = self._build_inline_arguments(field, field_def)
            
            # Check if attribute is callable and call with arguments
            self._emit(f"_attr = getattr({parent_var}, '{field_name}', None)")
            self._emit(f"if callable(_attr):")
            self.indent_level += 1
            if args_code:
                self._emit(f"_temp_val = _attr({args_code})")
            else:
                self._emit(f"_temp_val = _attr()")
            self.indent_level -= 1
            self._emit(f"else:")
            self.indent_level += 1
            self._emit(f"_temp_val = _attr")
            self.indent_level -= 1
            
            # Now handle the result
            if field.selection_set:
                self._process_nested_field(field, field_def, "_temp_val", result_var, alias)
            else:
                self._emit(f'{result_var}["{alias}"] = _temp_val')
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

        # Handle arguments for complex fields with resolvers
        if field.arguments or (field_def.args and len(field_def.args) > 0):
            args_code = self._build_inline_arguments(field, field_def)
            if args_code:
                self._emit(f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, None, {args_code})")
            else:
                self._emit(f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, None)")
        else:
            # No arguments - simple resolver call
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

    def _process_nested_field(self, field, field_def, temp_var, result_var, alias):
        """Process nested field selection."""
        field_type = field_def.type
        while hasattr(field_type, "of_type"):
            field_type = field_type.of_type

        if isinstance(field_type, GraphQLObjectType):
            self._emit(f"if {temp_var} is not None:")
            self.indent_level += 1

            # Handle lists
            if hasattr(field_def.type, "of_type") and str(field_def.type).startswith("["):
                self._emit(f"if isinstance({temp_var}, list):")
                self.indent_level += 1
                self._emit(f'{result_var}["{alias}"] = []')
                item_var = f"_item_{field.name.value}"
                item_result_var = f"_{field.name.value}_item_result"
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
                nested_var = f"_nested_{field.name.value}"
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

    def _build_inline_arguments(self, field: FieldNode, field_def) -> str:
        """Build inline arguments for optimized function calls."""
        args = []
        
        # Collect default values
        defaults = {}
        if field_def.args:
            for arg_name, arg_def in field_def.args.items():
                if hasattr(arg_def, 'default_value') and arg_def.default_value is not Undefined:
                    defaults[arg_name] = self._serialize_value(arg_def.default_value)
        
        # Override with provided arguments
        provided = {}
        if field.arguments:
            for arg in field.arguments:
                arg_name = arg.name.value
                provided[arg_name] = self._generate_argument_value(arg.value)
        
        # Merge defaults and provided
        all_args = {**defaults, **provided}
        
        # Format as keyword arguments
        for key, value in all_args.items():
            args.append(f"{key}={value}")
        
        return ", ".join(args) if args else ""
    
    def _generate_argument_value(self, value_node) -> str:
        """Generate inline code for argument values."""
        from graphql.language import (
            VariableNode,
            IntValueNode,
            FloatValueNode,
            StringValueNode,
            BooleanValueNode,
            NullValueNode,
            ListValueNode,
            ObjectValueNode,
            EnumValueNode,
        )
        
        if isinstance(value_node, VariableNode):
            # For optimized version, we'll access variables directly
            var_name = value_node.name.value
            return f"variables.get('{var_name}')"
        elif isinstance(value_node, (IntValueNode, FloatValueNode)):
            return value_node.value
        elif isinstance(value_node, StringValueNode):
            return repr(value_node.value)
        elif isinstance(value_node, BooleanValueNode):
            return "True" if value_node.value else "False"
        elif isinstance(value_node, NullValueNode):
            return "None"
        elif isinstance(value_node, EnumValueNode):
            return repr(value_node.value)
        elif isinstance(value_node, ListValueNode):
            items = [self._generate_argument_value(item) for item in value_node.values]
            return f"[{', '.join(items)}]"
        elif isinstance(value_node, ObjectValueNode):
            items = []
            for field in value_node.fields:
                key = repr(field.name.value)
                val = self._generate_argument_value(field.value)
                items.append(f"{key}: {val}")
            return f"{{{', '.join(items)}}}"
        else:
            return "None"
    
    def _serialize_value(self, value) -> str:
        """Serialize Python values for code generation."""
        if value is None:
            return "None"
        elif isinstance(value, bool):
            return "True" if value else "False"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return repr(value)
        elif isinstance(value, list):
            items = [self._serialize_value(item) for item in value]
            return f"[{', '.join(items)}]"
        elif isinstance(value, dict):
            items = [f"{repr(k)}: {self._serialize_value(v)}" for k, v in value.items()]
            return f"{{{', '.join(items)}}}"
        else:
            return repr(value)

    def _emit(self, line: str):
        indent = "    " * self.indent_level
        self.generated_code.append(f"{indent}{line}")


def compile_query_optimized(schema: GraphQLSchema, query: str) -> Callable:
    """Compile a GraphQL query with aggressive optimizations."""
    compiler = OptimizedGraphQLJITCompiler(schema)
    return compiler.compile_query(query)
