from typing import Any

from graphql import (
    ArgumentNode,
    GraphQLError,
    GraphQLNamedType,
    ObjectValueNode,
    ValidationContext,
    ValidationRule,
    get_named_type,
)

from strawberry.types.base import StrawberryMaybe, StrawberryOptional
from strawberry.utils.str_converters import to_camel_case


class MaybeNullValidationRule(ValidationRule):
    """Validates that Maybe[T] fields do not receive explicit null values.

    This rule ensures that:
    - Maybe[T] fields can only be omitted or have non-null values
    - Maybe[T | None] fields can be omitted, null, or have non-null values

    This provides clear semantics where Maybe[T] means "either present with value or absent"
    and Maybe[T | None] means "present with value, present but null, or absent".
    """

    def __init__(self, validation_context: ValidationContext) -> None:
        super().__init__(validation_context)

    def enter_argument(self, node: ArgumentNode, *_args: Any) -> None:
        # Check if this is a null value
        if node.value.kind != "null_value":
            return

        # Get the argument definition from the schema
        argument_def = self.context.get_argument()
        if not argument_def:
            return

        # Check if this argument corresponds to a Maybe[T] (not Maybe[T | None])
        # The argument type extensions should contain the Strawberry type info
        strawberry_arg_info = argument_def.extensions.get("strawberry-definition")
        if not strawberry_arg_info:
            return

        # Get the Strawberry type from the argument info
        field_type = getattr(strawberry_arg_info, "type", None)
        if not field_type:
            return

        if isinstance(field_type, StrawberryMaybe) and not isinstance(
            field_type.of_type, StrawberryOptional
        ):
            # This is Maybe[T] - should not accept null values
            type_name = self._get_type_name(field_type.of_type)

            self.report_error(
                GraphQLError(
                    f"Expected value of type '{type_name}', found null. "
                    f"Argument '{node.name.value}' of type 'Maybe[{type_name}]' cannot be explicitly set to null. "
                    f"Use 'Maybe[{type_name} | None]' if you need to allow null values.",
                    nodes=[node],
                )
            )

    def enter_object_value(self, node: ObjectValueNode, *_args: Any) -> None:
        # Get the input type for this object
        input_type = get_named_type(self.context.get_input_type())
        if not input_type:
            return

        # Get the Strawberry type definition from extensions
        strawberry_type = input_type.extensions.get("strawberry-definition")
        if not strawberry_type:
            return

        # Check each field in the object for null Maybe[T] violations
        self.validate_maybe_fields(node, input_type, strawberry_type)

    def validate_maybe_fields(
        self, node: ObjectValueNode, input_type: GraphQLNamedType, strawberry_type: Any
    ) -> None:
        # Create a map of field names to field nodes for easy lookup
        field_node_map = {field.name.value: field for field in node.fields}

        # Check each field in the Strawberry type definition
        if not hasattr(strawberry_type, "fields"):
            return

        for field_def in strawberry_type.fields:
            # Resolve the actual GraphQL field name using the same logic as NameConverter
            if field_def.graphql_name is not None:
                field_name = field_def.graphql_name
            else:
                # Apply auto_camel_case conversion if enabled (default behavior)
                field_name = to_camel_case(field_def.python_name)

            # Check if this field is present in the input and has a null value
            if field_name in field_node_map:
                field_node = field_node_map[field_name]

                # Check if this field has a null value
                if field_node.value.kind == "null_value":
                    # Check if this is a Maybe[T] (not Maybe[T | None])
                    field_type = field_def.type
                    if isinstance(field_type, StrawberryMaybe) and not isinstance(
                        field_type.of_type, StrawberryOptional
                    ):
                        # This is Maybe[T] - should not accept null values
                        type_name = self._get_type_name(field_type.of_type)
                        self.report_error(
                            GraphQLError(
                                f"Expected value of type '{type_name}', found null. "
                                f"Field '{field_name}' of type 'Maybe[{type_name}]' cannot be explicitly set to null. "
                                f"Use 'Maybe[{type_name} | None]' if you need to allow null values.",
                                nodes=[field_node],
                            )
                        )

    def _get_type_name(self, type_: Any) -> str:
        """Get a readable type name for error messages."""
        if hasattr(type_, "__name__"):
            return type_.__name__
        # Handle Strawberry types that don't have __name__
        if hasattr(type_, "of_type") and hasattr(type_.of_type, "__name__"):
            # For StrawberryList, StrawberryOptional, etc.
            return (
                f"list[{type_.of_type.__name__}]"
                if "List" in str(type_.__class__)
                else type_.of_type.__name__
            )
        return str(type_)


__all__ = ["MaybeNullValidationRule"]
