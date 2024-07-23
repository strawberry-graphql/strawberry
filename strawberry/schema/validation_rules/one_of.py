from typing import Any

from graphql import (
    ExecutableDefinitionNode,
    GraphQLError,
    GraphQLNamedType,
    ObjectValueNode,
    ValidationContext,
    ValidationRule,
    VariableDefinitionNode,
    get_named_type,
)


class OneOfInputValidationRule(ValidationRule):
    def __init__(self, validation_context: ValidationContext) -> None:
        super().__init__(validation_context)

    def enter_operation_definition(
        self, node: ExecutableDefinitionNode, *_args: Any
    ) -> None:
        self.variable_definitions: dict[str, VariableDefinitionNode] = {}

    def enter_variable_definition(
        self, node: VariableDefinitionNode, *_args: Any
    ) -> None:
        self.variable_definitions[node.variable.name.value] = node

    def enter_object_value(self, node: ObjectValueNode, *_args: Any) -> None:
        type_ = get_named_type(self.context.get_input_type())

        if not type_:
            return

        strawberry_type = type_.extensions.get("strawberry-definition")

        if strawberry_type and strawberry_type.is_one_of:
            self.validate_one_of(node, type_)

    def validate_one_of(self, node: ObjectValueNode, type: GraphQLNamedType) -> None:
        field_node_map = {field.name.value: field for field in node.fields}
        keys = list(field_node_map.keys())
        is_not_exactly_one_field = len(keys) != 1

        if is_not_exactly_one_field:
            self.report_error(
                GraphQLError(
                    f"OneOf Input Object '{type.name}' must specify exactly one key.",
                    nodes=[node],
                )
            )

            return

        value = field_node_map[keys[0]].value
        is_null_literal = not value or value.kind == "null_value"
        is_variable = value.kind == "variable"

        if is_null_literal:
            self.report_error(
                GraphQLError(
                    f"Field '{type.name}.{keys[0]}' must be non-null.",
                    nodes=[node],
                )
            )

            return

        if is_variable:
            variable_name = value.name.value  # type: ignore
            definition = self.variable_definitions[variable_name]
            is_nullable_variable = definition.type.kind != "non_null_type"

            if is_nullable_variable:
                self.report_error(
                    GraphQLError(
                        f"Variable '{variable_name}' must be non-nullable to be used for OneOf Input Object '{type.name}'.",
                        nodes=[node],
                    )
                )


__all__ = ["OneOfInputValidationRule"]
