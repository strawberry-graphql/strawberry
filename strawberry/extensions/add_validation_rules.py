from typing import List, Type

from graphql import ASTValidationRule

from strawberry.extensions.base_extension import Extension


class AddValidationRules(Extension):
    """
    Add graphql-core validation rules

    Example:

    >>> import strawberry
    >>> from strawberry.extensions import AddValidationRules
    >>> from graphql import ValidationRule, GraphQLError
    >>>
    >>> class MyCustomRule(ValidationRule):
    ...     def enter_field(self, node, *args) -> None:
    ...         if node.name.value == "secret_field":
    ...             self.report_error(
    ...                 GraphQLError("Can't query field 'secret_field'")
    ...             )
    >>>
    >>> schema = strawberry.Schema(
    ...     Query,
    ...     extensions=[
    ...         AddValidationRules([
    ...             MyCustomRule,
    ...         ]),
    ...     ]
    ... )

    """

    validation_rules: List[Type[ASTValidationRule]]

    def __init__(self, validation_rules: List[Type[ASTValidationRule]]):
        self.validation_rules = validation_rules

    def on_request_start(self) -> None:
        self.execution_context.validation_rules = (
            self.execution_context.validation_rules + tuple(self.validation_rules)
        )
