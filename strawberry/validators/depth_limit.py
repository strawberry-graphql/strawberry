import re
from typing import Callable, List, Union

from graphql import GraphQLError
from graphql.language import (
    DefinitionNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    OperationDefinitionNode,
)
from graphql.validation import ValidationContext, ValidationRule


def depth_limit(max_depth: int, options=None, callback=None):
    """
    Creates a validator for the GraphQL query depth

    - max_depth - The maximum allowed depth for any operation in a GraphQL document.
    - options
        - options.ignore - Stops recursive depth checking based on a field name.
        Either a string or regexp to match the name, or a function that returns
        a boolean.
    - callback - Called each time validation runs. Receives an Object which is a
    map of the depths for each operation.
    """
    if not options:
        options = {}

    class DepthLimitValidator(ValidationRule):
        def __init__(self, validation_context: ValidationContext):
            document = validation_context.document
            definitions = document.definitions

            fragments = get_fragments(definitions)
            queries = get_queries_and_mutations(definitions)
            query_depths = {}

            for name in queries:
                query_depths[name] = determine_depth(
                    queries[name],
                    fragments,
                    0,
                    max_depth,
                    validation_context,
                    name,
                    options,
                )

            callback(query_depths)
            super().__init__(validation_context)

    return DepthLimitValidator


def get_fragments(definitions: List[DefinitionNode]):
    fragments = {}
    for definition in definitions:
        if isinstance(definition, FragmentDefinitionNode):
            fragments[definition.name.value] = definition

    return fragments


# This will actually get both queries and mutations.
# We can basically treat those the same
def get_queries_and_mutations(definitions: List[DefinitionNode]):
    operations = {}

    for definition in definitions:
        if isinstance(definition, OperationDefinitionNode):
            operations[definition.name.value if definition.name else ""] = definition

    return operations


introspection_regex = re.compile(r"^__")


def determine_depth(
    node, fragments, depth_so_far, max_depth, context, operation_name, options
) -> int:
    if depth_so_far > max_depth:
        context.report_error(
            GraphQLError(
                f"'{operation_name}' exceeds maximum operation depth of {max_depth}",
                [node],
            )
        )
        return depth_so_far

    if isinstance(node, FieldNode):
        # by default, ignore the introspection fields which begin with double underscores
        should_ignore = introspection_regex.match(node.name.value) or see_if_ignored(
            node, options.get("ignore", [])
        )

        if should_ignore or not node.selection_set:
            return 0

        return 1 + max(
            map(
                lambda selection: determine_depth(
                    selection,
                    fragments,
                    depth_so_far + 1,
                    max_depth,
                    context,
                    operation_name,
                    options,
                ),
                node.selection_set.selections,
            )
        )
    elif isinstance(node, FragmentSpreadNode):
        return determine_depth(
            fragments[node.name.value],
            fragments,
            depth_so_far,
            max_depth,
            context,
            operation_name,
            options,
        )
    elif (
        isinstance(node, InlineFragmentNode)
        or isinstance(node, FragmentDefinitionNode)
        or isinstance(node, OperationDefinitionNode)
    ):
        return max(
            map(
                lambda selection: determine_depth(
                    selection,
                    fragments,
                    depth_so_far,
                    max_depth,
                    context,
                    operation_name,
                    options,
                ),
                node.selection_set.selections,
            )
        )
    else:
        raise Exception(f"uh oh! depth crawler cannot handle: {node.kind}")


def see_if_ignored(
    node, ignore: List[Union[Callable[[str], bool], re.Pattern, str]]
) -> bool:
    for rule in ignore:
        field_name = node.name.value
        if isinstance(rule, str):
            if field_name == rule:
                return True
        elif isinstance(rule, re.Pattern):
            if rule.match(field_name):
                return True
        elif callable(rule):
            if rule(field_name):
                return True
        else:
            raise Exception(f"Invalid ignore option: {rule}")

    return False
