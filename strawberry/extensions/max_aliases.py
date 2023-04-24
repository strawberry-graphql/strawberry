from typing import Type

from graphql import (
    ExecutableDefinitionNode,
    FieldNode,
    GraphQLError,
    InlineFragmentNode,
    ValidationContext,
    ValidationRule,
)

from strawberry.extensions.add_validation_rules import AddValidationRules


class MaxAliasesLimiter(AddValidationRules):
    """
    Add a validator to limit the number of aliases used.

    Example:

    >>> import strawberry
    >>> from strawberry.extensions import QueryDepthLimiter
    >>>
    >>> schema = strawberry.Schema(
    ...     Query,
    ...     extensions=[
    ...         MaxAliasesLimiter(max_alias_count=15)
    ...     ]
    ... )

    Arguments:

    `max_alias_count: int`
        The maximum number of aliases allowed in a GraphQL document.
    """

    def __init__(
        self,
        max_alias_count: int,
    ):
        validator = create_validator(max_alias_count)
        super().__init__([validator])


def create_validator(max_alias_count: int) -> Type[ValidationRule]:
    class MaxAliasesValidator(ValidationRule):
        def __init__(self, validation_context: ValidationContext):
            document = validation_context.document
            def_that_can_contain_alias = [
                def_
                for def_ in document.definitions
                if isinstance(def_, (ExecutableDefinitionNode))
            ]
            total_aliases = sum(
                count_fields_with_alias(def_node)
                for def_node in def_that_can_contain_alias
            )
            if total_aliases > max_alias_count:
                msg = f"{total_aliases} aliases found. Allowed: {max_alias_count}"
                validation_context.report_error(GraphQLError(msg))

            super().__init__(validation_context)

    return MaxAliasesValidator


def count_fields_with_alias(selection_set_owner) -> int:
    result = 0
    for sel in selection_set_owner.selection_set.selections:
        if isinstance(sel, FieldNode) and sel.alias:
            result += 1
        if isinstance(sel, (FieldNode, InlineFragmentNode)) and sel.selection_set:
            result += count_fields_with_alias(sel)
    return result
