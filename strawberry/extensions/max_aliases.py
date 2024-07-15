from typing import Type, Union

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
    """Add a validator to limit the number of aliases used.

    Example:

    ```python
    import strawberry
    from strawberry.extensions import MaxAliasesLimiter

    schema = strawberry.Schema(Query, extensions=[MaxAliasesLimiter(max_alias_count=15)])
    ```
    """

    def __init__(self, max_alias_count: int) -> None:
        """Initialize the MaxAliasesLimiter.

        Args:
            max_alias_count: The maximum number of aliases allowed in a GraphQL document.
        """
        validator = create_validator(max_alias_count)
        super().__init__([validator])


def create_validator(max_alias_count: int) -> Type[ValidationRule]:
    """Create a validator that checks the number of aliases in a document.

    Args:
        max_alias_count: The maximum number of aliases allowed in a GraphQL document.
    """

    class MaxAliasesValidator(ValidationRule):
        def __init__(self, validation_context: ValidationContext) -> None:
            document = validation_context.document
            def_that_can_contain_alias = (
                def_
                for def_ in document.definitions
                if isinstance(def_, (ExecutableDefinitionNode))
            )
            total_aliases = sum(
                count_fields_with_alias(def_node)
                for def_node in def_that_can_contain_alias
            )
            if total_aliases > max_alias_count:
                msg = f"{total_aliases} aliases found. Allowed: {max_alias_count}"
                validation_context.report_error(GraphQLError(msg))

            super().__init__(validation_context)

    return MaxAliasesValidator


def count_fields_with_alias(
    selection_set_owner: Union[ExecutableDefinitionNode, FieldNode, InlineFragmentNode],
) -> int:
    if selection_set_owner.selection_set is None:
        return 0

    result = 0

    for selection in selection_set_owner.selection_set.selections:
        if isinstance(selection, FieldNode) and selection.alias:
            result += 1
        if (
            isinstance(selection, (FieldNode, InlineFragmentNode))
            and selection.selection_set
        ):
            result += count_fields_with_alias(selection)

    return result


__all__ = ["MaxAliasesLimiter"]
