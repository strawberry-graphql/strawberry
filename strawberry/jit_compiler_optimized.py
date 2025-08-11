from __future__ import annotations

import inspect
from typing import Callable, Optional, Set

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
        self.fragments = {}  # Maps fragment names to their definitions
        self.has_async_resolvers = False  # Track if we have any async resolvers
        self.async_resolver_ids: Set[str] = set()  # Track which resolvers are async

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

        # Reset state
        self.generated_code = []
        self.indent_level = 0
        self.field_counter = 0
        self.resolver_map = {}
        self.inline_resolvers = {}
        self.has_async_resolvers = False
        self.async_resolver_ids = set()

        function_code = self._generate_optimized_function(operation, root_type)

        # Create minimal runtime environment
        local_vars = {
            "_resolvers": self.resolver_map,
            "_async_resolver_ids": self.async_resolver_ids,
            "getattr": getattr,  # Direct access to builtins
            "hasattr": hasattr,
            "isinstance": isinstance,
            "len": len,
        }
        
        # Add asyncio if we have async resolvers
        if self.has_async_resolvers:
            import asyncio
            local_vars["asyncio"] = asyncio

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
        
        # First pass: analyze for async resolvers
        self._analyze_async_resolvers(operation.selection_set, root_type)
        
        # Reset for actual generation
        self.generated_code = []
        self.indent_level = 0

        if self.has_async_resolvers:
            self._emit("async def execute_query(root, context=None, variables=None):")
        else:
            self._emit("def execute_query(root, context=None, variables=None):")
        self.indent_level += 1
        self._emit("result = {}")

        if operation.selection_set:
            if self.has_async_resolvers:
                self._generate_optimized_selection_set_async(
                    operation.selection_set, root_type, "root", "result"
                )
            else:
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
        fragment_spreads = []
        inline_fragments = []

        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                field_def = parent_type.fields.get(field_name)

                if field_def and not field_def.resolve:
                    # Group simple fields for batch processing
                    fields_by_resolver_type.setdefault("simple", []).append(selection)
                else:
                    fields_by_resolver_type.setdefault("complex", []).append(selection)
            elif isinstance(selection, FragmentSpreadNode):
                fragment_spreads.append(selection)
            elif isinstance(selection, InlineFragmentNode):
                inline_fragments.append(selection)

        # Process simple fields first (batch them)
        if "simple" in fields_by_resolver_type:
            for field in fields_by_resolver_type["simple"]:
                self._generate_simple_field(field, parent_type, parent_var, result_var)

        # Process complex fields
        if "complex" in fields_by_resolver_type:
            for field in fields_by_resolver_type["complex"]:
                self._generate_complex_field(field, parent_type, parent_var, result_var)

        # Process fragment spreads
        for fragment_spread in fragment_spreads:
            self._generate_fragment_spread(
                fragment_spread, parent_type, parent_var, result_var
            )

        # Process inline fragments
        for inline_fragment in inline_fragments:
            self._generate_inline_fragment(
                inline_fragment, parent_type, parent_var, result_var
            )

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
        
        # Handle directives (@skip and @include)
        directive_check = None
        if field.directives:
            directive_check = self._generate_directive_check(field.directives)
            if directive_check:
                self._emit(f"if {directive_check}:")
                self.indent_level += 1

        # Handle field arguments for simple fields (methods)
        if field.arguments or (field_def.args and len(field_def.args) > 0):
            # Build arguments dictionary inline for optimization
            args_code = self._build_inline_arguments(field, field_def)

            # Check if attribute is callable and call with arguments
            self._emit(f"_attr = getattr({parent_var}, '{field_name}', None)")
            self._emit("if callable(_attr):")
            self.indent_level += 1
            if args_code:
                self._emit(f"_temp_val = _attr({args_code})")
            else:
                self._emit("_temp_val = _attr()")
            self.indent_level -= 1
            self._emit("else:")
            self.indent_level += 1
            self._emit("_temp_val = _attr")
            self.indent_level -= 1

            # Now handle the result
            if field.selection_set:
                self._process_nested_field(
                    field, field_def, "_temp_val", result_var, alias
                )
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
        
        # Close directive conditional block if needed
        if field.directives and directive_check:
            self.indent_level -= 1

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
        
        # Handle directives (@skip and @include)
        directive_check = None
        if field.directives:
            directive_check = self._generate_directive_check(field.directives)
            if directive_check:
                self._emit(f"if {directive_check}:")
                self.indent_level += 1

        resolver_id = f"resolver_{self.field_counter}"
        self.field_counter += 1
        self.resolver_map[resolver_id] = field_def.resolve
        
        # Check if resolver is async
        if inspect.iscoroutinefunction(field_def.resolve):
            self.has_async_resolvers = True
            self.async_resolver_ids.add(resolver_id)

        temp_var = f"_field_{field_name}"

        # Handle arguments for complex fields with resolvers
        if field.arguments or (field_def.args and len(field_def.args) > 0):
            args_code = self._build_inline_arguments(field, field_def)
            if args_code:
                self._emit(
                    f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, None, {args_code})"
                )
            else:
                self._emit(
                    f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, None)"
                )
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
        
        # Close directive conditional block if needed
        if field.directives and directive_check:
            self.indent_level -= 1

    def _process_nested_field(self, field, field_def, temp_var, result_var, alias):
        """Process nested field selection."""
        field_type = field_def.type
        while hasattr(field_type, "of_type"):
            field_type = field_type.of_type

        if isinstance(field_type, GraphQLObjectType):
            self._emit(f"if {temp_var} is not None:")
            self.indent_level += 1

            # Handle lists
            if hasattr(field_def.type, "of_type") and str(field_def.type).startswith(
                "["
            ):
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
                if (
                    hasattr(arg_def, "default_value")
                    and arg_def.default_value is not Undefined
                ):
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
            # For optimized version, we'll access variables directly
            var_name = value_node.name.value
            return f"variables.get('{var_name}')"
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
            items = [self._generate_argument_value(item) for item in value_node.values]
            return f"[{', '.join(items)}]"
        if isinstance(value_node, ObjectValueNode):
            items = []
            for field in value_node.fields:
                key = repr(field.name.value)
                val = self._generate_argument_value(field.value)
                items.append(f"{key}: {val}")
            return f"{{{', '.join(items)}}}"
        return "None"

    def _serialize_value(self, value) -> str:
        """Serialize Python values for code generation."""
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

    def _extract_fragments(self, document: DocumentNode):
        """Extract fragment definitions from the document."""
        self.fragments = {}
        for definition in document.definitions:
            if isinstance(definition, FragmentDefinitionNode):
                self.fragments[definition.name.value] = definition

    def _generate_directive_check(self, directives: list[DirectiveNode]) -> str:
        """Generate optimized conditional expression for @skip and @include directives."""
        conditions = []
        
        for directive in directives:
            directive_name = directive.name.value
            
            if directive_name == "skip":
                # @skip(if: condition) - skip field if condition is true
                if_arg = self._get_directive_if_argument(directive)
                if if_arg:
                    conditions.append(f"not ({if_arg})")
            elif directive_name == "include":
                # @include(if: condition) - include field if condition is true  
                if_arg = self._get_directive_if_argument(directive)
                if if_arg:
                    conditions.append(if_arg)
        
        if conditions:
            # Combine conditions with AND for optimal performance
            return " and ".join(conditions)
        return ""
    
    def _get_directive_if_argument(self, directive: DirectiveNode) -> str:
        """Extract the 'if' argument value from a directive."""
        for arg in directive.arguments or []:
            if arg.name.value == "if":
                return self._generate_argument_value(arg.value)
        return ""
    
    def _emit(self, line: str):
        indent = "    " * self.indent_level
        self.generated_code.append(f"{indent}{line}")

    def _generate_fragment_spread(
        self,
        fragment_spread: FragmentSpreadNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
    ):
        """Generate optimized code for a fragment spread."""
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
                self._generate_optimized_selection_set(
                    fragment_def.selection_set,
                    parent_type,
                    parent_var,
                    result_var,
                )
        else:
            # Generate a type check for the fragment
            self._emit(f"# Fragment spread: {fragment_name}")
            self._emit(
                f"if hasattr({parent_var}, '__typename') and {parent_var}.__typename == '{type_condition}':"
            )
            self.indent_level += 1
            if fragment_def.selection_set:
                self._generate_optimized_selection_set(
                    fragment_def.selection_set,
                    parent_type,
                    parent_var,
                    result_var,
                )
            self.indent_level -= 1

    def _generate_inline_fragment(
        self,
        inline_fragment: InlineFragmentNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
    ):
        """Generate optimized code for an inline fragment."""
        # Check if there's a type condition
        if inline_fragment.type_condition:
            type_name = inline_fragment.type_condition.name.value

            # Get the actual type from schema
            fragment_type = self.schema.type_map.get(type_name)
            if not fragment_type or not isinstance(fragment_type, GraphQLObjectType):
                return  # Skip if type not found

            # If the type condition matches the parent type, apply directly
            if type_name == parent_type.name:
                # Same type, no need for runtime check - optimize by inlining
                self._emit(f"# Inline fragment on {type_name} (optimized)")
                if inline_fragment.selection_set:
                    self._generate_optimized_selection_set(
                        inline_fragment.selection_set,
                        fragment_type,
                        parent_var,
                        result_var,
                    )
            else:
                # Different type, need runtime check
                self._emit(f"# Inline fragment on {type_name}")
                self._emit(
                    f"if hasattr({parent_var}, '__typename') and {parent_var}.__typename == '{type_name}':"
                )
                self.indent_level += 1

                if inline_fragment.selection_set:
                    self._generate_optimized_selection_set(
                        inline_fragment.selection_set,
                        fragment_type,
                        parent_var,
                        result_var,
                    )

                self.indent_level -= 1
        # No type condition, apply selections directly
        elif inline_fragment.selection_set:
            self._generate_optimized_selection_set(
                inline_fragment.selection_set,
                parent_type,
                parent_var,
                result_var,
            )
    
    def _analyze_async_resolvers(self, selection_set: SelectionSetNode, parent_type: GraphQLObjectType):
        """Analyze selection set for async resolvers."""
        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                field_def = parent_type.fields.get(field_name)
                
                if field_def and field_def.resolve:
                    # Check if resolver is async
                    if inspect.iscoroutinefunction(field_def.resolve):
                        self.has_async_resolvers = True
                        
                # Recurse into nested selections
                if field_def and selection.selection_set:
                    field_type = field_def.type
                    while hasattr(field_type, "of_type"):
                        field_type = field_type.of_type
                    
                    if isinstance(field_type, GraphQLObjectType):
                        self._analyze_async_resolvers(selection.selection_set, field_type)
            
            elif isinstance(selection, FragmentSpreadNode):
                fragment_name = selection.name.value
                if fragment_name in self.fragments:
                    fragment_def = self.fragments[fragment_name]
                    if fragment_def.selection_set:
                        # Get the fragment type
                        type_name = fragment_def.type_condition.name.value
                        fragment_type = self.schema.type_map.get(type_name)
                        if fragment_type and isinstance(fragment_type, GraphQLObjectType):
                            self._analyze_async_resolvers(fragment_def.selection_set, fragment_type)
            
            elif isinstance(selection, InlineFragmentNode):
                if selection.type_condition:
                    type_name = selection.type_condition.name.value
                    fragment_type = self.schema.type_map.get(type_name)
                    if fragment_type and isinstance(fragment_type, GraphQLObjectType) and selection.selection_set:
                        self._analyze_async_resolvers(selection.selection_set, fragment_type)
                elif selection.selection_set:
                    self._analyze_async_resolvers(selection.selection_set, parent_type)
    
    def _generate_optimized_selection_set_async(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
    ):
        """Generate optimized async selection set code."""
        # Group fields by type for potential batching
        simple_fields = []
        async_fields = []
        sync_fields = []
        fragment_spreads = []
        inline_fragments = []
        
        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                field_def = parent_type.fields.get(field_name)
                
                if field_def and not field_def.resolve:
                    # Simple field with no resolver
                    simple_fields.append(selection)
                elif field_def and field_def.resolve:
                    # Check if resolver is async
                    if inspect.iscoroutinefunction(field_def.resolve):
                        async_fields.append(selection)
                    else:
                        sync_fields.append(selection)
            elif isinstance(selection, FragmentSpreadNode):
                fragment_spreads.append(selection)
            elif isinstance(selection, InlineFragmentNode):
                inline_fragments.append(selection)
        
        # Process simple fields first (batch them)
        for field in simple_fields:
            self._generate_simple_field_async(field, parent_type, parent_var, result_var)
        
        # Process sync fields
        for field in sync_fields:
            self._generate_complex_field_async(field, parent_type, parent_var, result_var, is_async=False)
        
        # Process async fields - can be parallelized
        if async_fields:
            # Generate parallel async execution
            self._emit("# Execute async fields in parallel")
            self._emit("_async_tasks = []")
            
            for field in async_fields:
                self._generate_async_field_task(field, parent_type, parent_var)
            
            # Wait for all async tasks
            self._emit("if _async_tasks:")
            self.indent_level += 1
            self._emit("_async_results = await asyncio.gather(*_async_tasks)")
            self._emit("for field_alias, field_value in _async_results:")
            self.indent_level += 1
            self._emit(f"{result_var}[field_alias] = field_value")
            self.indent_level -= 1
            self.indent_level -= 1
        
        # Process fragments
        for fragment_spread in fragment_spreads:
            self._generate_fragment_spread_async(
                fragment_spread, parent_type, parent_var, result_var
            )
        
        for inline_fragment in inline_fragments:
            self._generate_inline_fragment_async(
                inline_fragment, parent_type, parent_var, result_var
            )
    
    def _generate_simple_field_async(
        self,
        field: FieldNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
    ):
        """Generate optimized code for simple field access in async context."""
        # For simple fields, just use the sync version - no await needed
        self._generate_simple_field(field, parent_type, parent_var, result_var)
    
    def _generate_complex_field_async(
        self,
        field: FieldNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
        is_async: bool = False,
    ):
        """Generate code for fields with custom resolvers in async context."""
        field_name = field.name.value
        alias = field.alias.value if field.alias else field_name
        
        field_def = parent_type.fields.get(field_name)
        if not field_def:
            return
        
        # Handle directives
        directive_check = None
        if field.directives:
            directive_check = self._generate_directive_check(field.directives)
            if directive_check:
                self._emit(f"if {directive_check}:")
                self.indent_level += 1
        
        resolver_id = f"resolver_{self.field_counter}"
        self.field_counter += 1
        self.resolver_map[resolver_id] = field_def.resolve
        
        # Check if resolver is async
        if inspect.iscoroutinefunction(field_def.resolve):
            self.async_resolver_ids.add(resolver_id)
        
        temp_var = f"_field_{field_name}"
        
        # Generate resolver call with await if needed
        args_code = ""
        if field.arguments or (field_def.args and len(field_def.args) > 0):
            args_code = self._build_inline_arguments(field, field_def)
        
        if is_async or resolver_id in self.async_resolver_ids:
            # Async resolver - use await
            if args_code:
                self._emit(
                    f"{temp_var} = await _resolvers['{resolver_id}']({parent_var}, None, {args_code})"
                )
            else:
                self._emit(
                    f"{temp_var} = await _resolvers['{resolver_id}']({parent_var}, None)"
                )
        else:
            # Sync resolver - no await
            if args_code:
                self._emit(
                    f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, None, {args_code})"
                )
            else:
                self._emit(
                    f"{temp_var} = _resolvers['{resolver_id}']({parent_var}, None)"
                )
        
        # Process result
        if field.selection_set:
            field_type = field_def.type
            while hasattr(field_type, "of_type"):
                field_type = field_type.of_type
            
            if isinstance(field_type, GraphQLObjectType):
                self._emit(f"if {temp_var} is not None:")
                self.indent_level += 1
                
                if hasattr(field_def.type, "of_type") and str(field_def.type).startswith("["):
                    # Handle list
                    self._emit(f"if isinstance({temp_var}, list):")
                    self.indent_level += 1
                    self._emit(f'{result_var}["{alias}"] = []')
                    item_var = f"_item_{field_name}"
                    item_result_var = f"_{field_name}_item_result"
                    self._emit(f"for {item_var} in {temp_var}:")
                    self.indent_level += 1
                    self._emit(f"{item_result_var} = {{}}")
                    # Use async version for nested selections
                    self._generate_optimized_selection_set_async(
                        field.selection_set, field_type, item_var, item_result_var
                    )
                    self._emit(f'{result_var}["{alias}"].append({item_result_var})')
                    self.indent_level -= 1
                    self.indent_level -= 1
                else:
                    # Handle object
                    nested_var = f"_nested_{field_name}"
                    self._emit(f"{nested_var} = {{}}")
                    self._generate_optimized_selection_set_async(
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
        
        # Close directive block
        if field.directives and directive_check:
            self.indent_level -= 1
    
    def _generate_async_field_task(
        self,
        field: FieldNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
    ):
        """Generate an async task for parallel execution."""
        field_name = field.name.value
        alias = field.alias.value if field.alias else field_name
        
        field_def = parent_type.fields.get(field_name)
        if not field_def:
            return
        
        resolver_id = f"resolver_{self.field_counter}"
        self.field_counter += 1
        self.resolver_map[resolver_id] = field_def.resolve
        self.async_resolver_ids.add(resolver_id)
        
        # Build arguments
        args_code = ""
        if field.arguments or (field_def.args and len(field_def.args) > 0):
            args_code = self._build_inline_arguments(field, field_def)
        
        # Create async task
        task_name = f"_task_{field_name}_{self.field_counter}"
        self._emit(f"async def {task_name}():")
        self.indent_level += 1
        
        if args_code:
            self._emit(f"value = await _resolvers['{resolver_id}']({parent_var}, None, {args_code})")
        else:
            self._emit(f"value = await _resolvers['{resolver_id}']({parent_var}, None)")
        
        # Handle nested selections inline if needed
        if field.selection_set:
            field_type = field_def.type
            while hasattr(field_type, "of_type"):
                field_type = field_type.of_type
            
            if isinstance(field_type, GraphQLObjectType):
                self._emit("if value is not None:")
                self.indent_level += 1
                
                if hasattr(field_def.type, "of_type") and str(field_def.type).startswith("["):
                    # Handle list
                    self._emit("if isinstance(value, list):")
                    self.indent_level += 1
                    self._emit("result_list = []")
                    self._emit("for item in value:")
                    self.indent_level += 1
                    self._emit("item_result = {}")
                    # Generate selections for each item
                    # Use a different variable name to avoid scoping issues
                    temp_item_var = f"_temp_item_{field_name}"
                    self._emit(f"{temp_item_var} = item")
                    self._generate_optimized_selection_set_async(
                        field.selection_set, field_type, temp_item_var, "item_result"
                    )
                    self._emit("result_list.append(item_result)")
                    self.indent_level -= 1
                    self._emit("processed_value = result_list")
                    self.indent_level -= 1
                else:
                    # Handle object - use a temporary variable to avoid scoping issues
                    self._emit("nested_result = {}")
                    temp_obj_var = f"_temp_obj_{field_name}"
                    self._emit(f"{temp_obj_var} = value")
                    self._generate_optimized_selection_set_async(
                        field.selection_set, field_type, temp_obj_var, "nested_result"
                    )
                    self._emit("processed_value = nested_result")
                
                self.indent_level -= 1
        
        # Return tuple with alias and processed value
        if field.selection_set:
            self._emit(f"return ('{alias}', processed_value if value is not None else value)")
        else:
            self._emit(f"return ('{alias}', value)")
        
        self.indent_level -= 1
        self._emit(f"_async_tasks.append({task_name}())")
    
    def _generate_fragment_spread_async(
        self,
        fragment_spread: FragmentSpreadNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
    ):
        """Generate async code for fragment spread."""
        fragment_name = fragment_spread.name.value
        
        if fragment_name not in self.fragments:
            raise ValueError(f"Fragment '{fragment_name}' not found")
        
        fragment_def = self.fragments[fragment_name]
        type_condition = fragment_def.type_condition.name.value
        
        if parent_type.name == type_condition:
            if fragment_def.selection_set:
                self._generate_optimized_selection_set_async(
                    fragment_def.selection_set,
                    parent_type,
                    parent_var,
                    result_var,
                )
        else:
            self._emit(f"# Fragment spread: {fragment_name}")
            self._emit(
                f"if hasattr({parent_var}, '__typename') and {parent_var}.__typename == '{type_condition}':"
            )
            self.indent_level += 1
            if fragment_def.selection_set:
                self._generate_optimized_selection_set_async(
                    fragment_def.selection_set,
                    parent_type,
                    parent_var,
                    result_var,
                )
            self.indent_level -= 1
    
    def _generate_inline_fragment_async(
        self,
        inline_fragment: InlineFragmentNode,
        parent_type: GraphQLObjectType,
        parent_var: str,
        result_var: str,
    ):
        """Generate async code for inline fragment."""
        if inline_fragment.type_condition:
            type_name = inline_fragment.type_condition.name.value
            fragment_type = self.schema.type_map.get(type_name)
            
            if not fragment_type or not isinstance(fragment_type, GraphQLObjectType):
                return
            
            if type_name == parent_type.name:
                self._emit(f"# Inline fragment on {type_name} (optimized)")
                if inline_fragment.selection_set:
                    self._generate_optimized_selection_set_async(
                        inline_fragment.selection_set,
                        fragment_type,
                        parent_var,
                        result_var,
                    )
            else:
                self._emit(f"# Inline fragment on {type_name}")
                self._emit(
                    f"if hasattr({parent_var}, '__typename') and {parent_var}.__typename == '{type_name}':"
                )
                self.indent_level += 1
                if inline_fragment.selection_set:
                    self._generate_optimized_selection_set_async(
                        inline_fragment.selection_set,
                        fragment_type,
                        parent_var,
                        result_var,
                    )
                self.indent_level -= 1
        elif inline_fragment.selection_set:
            self._generate_optimized_selection_set_async(
                inline_fragment.selection_set,
                parent_type,
                parent_var,
                result_var,
            )


def compile_query_optimized(schema: GraphQLSchema, query: str) -> Callable:
    """Compile a GraphQL query with aggressive optimizations and async support."""
    compiler = OptimizedGraphQLJITCompiler(schema)
    return compiler.compile_query(query)
