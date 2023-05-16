# This is a Python port of https://github.com/stems/graphql-depth-limit
# which is licensed under the terms of the MIT license, reproduced below.
#
# -----------
#
# MIT License
#
# Copyright (c) 2017 Stem
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Type,
    Union,
)

from graphql import GraphQLError
from graphql.language import (
    BooleanValueNode,
    DefinitionNode,
    FieldNode,
    FloatValueNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    IntValueNode,
    ListValueNode,
    Node,
    ObjectValueNode,
    OperationDefinitionNode,
    StringValueNode,
    ValueNode,
)
from graphql.validation import ValidationContext, ValidationRule

from strawberry.extensions import AddValidationRules
from strawberry.extensions.utils import is_introspection_key

IgnoreType = Union[Callable[[str], bool], re.Pattern, str]

FieldArgumentType = Union[
    bool, int, float, str, List["FieldArgumentType"], Dict[str, "FieldArgumentType"]
]
FieldArgumentsType = Dict[str, FieldArgumentType]


@dataclass
class IgnoreContext:
    field_name: str
    field_args: FieldArgumentsType
    node: Node
    context: ValidationContext


ShouldIgnoreType = Callable[[IgnoreContext], bool]


class QueryDepthLimiter(AddValidationRules):
    """
    Add a validator to limit the query depth of GraphQL operations

    Example:

    >>> import strawberry
    >>> from strawberry.extensions import QueryDepthLimiter
    >>>
    >>> schema = strawberry.Schema(
    ...     Query,
    ...     extensions=[
    ...         QueryDepthLimiter(max_depth=4)
    ...     ]
    ... )

    Arguments:

    `max_depth: int`
        The maximum allowed depth for any operation in a GraphQL document.
    `ignore: Optional[List[IgnoreType]] DEPRECATED`
        Stops recursive depth checking based on a field name.
        Either a string or regexp to match the name, or a function that returns
        a boolean.
    `callback: Optional[Callable[[Dict[str, int]], None]`
        Called each time validation runs. Receives an Object which is a
        map of the depths for each operation.
    `should_ignore: Optional[ShouldIgnoreType]`
        Stops recursive depth checking based on a field name and arguments.
        A function that returns a boolean and conforms to the ShouldIgnoreType
        function signature.
    """

    def __init__(
        self,
        max_depth: int,
        ignore: Optional[List[IgnoreType]] = None,  # DEPRECATED
        callback: Optional[Callable[[Dict[str, int]], None]] = None,
        should_ignore: Optional[ShouldIgnoreType] = None,
    ):
        if should_ignore is not None:
            if not callable(should_ignore):
                raise TypeError(
                    "The `should_ignore` argument to "
                    "`QueryDepthLimiter` must be a callable."
                )
            validator = create_validator(max_depth, should_ignore, callback)
        else:
            warnings.warn(
                "The `ignore` argument to `QueryDepthLimiter` is deprecated. "
                "Please use `should_ignore` instead.",
                DeprecationWarning,
                stacklevel=1,
            )
            validator = create_validator_deprecated(max_depth, ignore, callback)
        super().__init__([validator])


def create_validator(
    max_depth: int,
    should_ignore: Optional[ShouldIgnoreType],
    callback: Optional[Callable[[Dict[str, int]], None]] = None,
) -> Type[ValidationRule]:
    class DepthLimitValidator(ValidationRule):
        def __init__(self, validation_context: ValidationContext):
            document = validation_context.document
            definitions = document.definitions

            fragments = get_fragments(definitions)
            queries = get_queries_and_mutations(definitions)
            query_depths = {}

            for query in queries:
                query_depths[query] = determine_depth(
                    node=queries[query],
                    fragments=fragments,
                    depth_so_far=0,
                    max_depth=max_depth,
                    context=validation_context,
                    operation_name=query,
                    should_ignore=should_ignore,
                )

            if callable(callback):
                callback(query_depths)
            super().__init__(validation_context)

    return DepthLimitValidator


def get_fragments(
    definitions: Iterable[DefinitionNode],
) -> Dict[str, FragmentDefinitionNode]:
    fragments = {}
    for definition in definitions:
        if isinstance(definition, FragmentDefinitionNode):
            fragments[definition.name.value] = definition

    return fragments


# This will actually get both queries and mutations.
# We can basically treat those the same
def get_queries_and_mutations(
    definitions: Iterable[DefinitionNode],
) -> Dict[str, OperationDefinitionNode]:
    operations = {}

    for definition in definitions:
        if isinstance(definition, OperationDefinitionNode):
            operation = definition.name.value if definition.name else "anonymous"
            operations[operation] = definition

    return operations


def get_field_name(
    node: FieldNode,
) -> str:
    return node.alias.value if node.alias else node.name.value


def resolve_field_value(
    value: ValueNode,
) -> FieldArgumentType:
    if isinstance(value, StringValueNode):
        return value.value
    elif isinstance(value, IntValueNode):
        return int(value.value)
    elif isinstance(value, FloatValueNode):
        return float(value.value)
    elif isinstance(value, BooleanValueNode):
        return value.value
    elif isinstance(value, ListValueNode):
        return [resolve_field_value(v) for v in value.values]
    elif isinstance(value, ObjectValueNode):
        return {v.name.value: resolve_field_value(v.value) for v in value.fields}
    else:
        return {}


def get_field_arguments(
    node: FieldNode,
) -> FieldArgumentsType:
    args_dict: FieldArgumentsType = {}
    for arg in node.arguments:
        args_dict[arg.name.value] = resolve_field_value(arg.value)
    return args_dict


def determine_depth(
    node: Node,
    fragments: Dict[str, FragmentDefinitionNode],
    depth_so_far: int,
    max_depth: int,
    context: ValidationContext,
    operation_name: str,
    should_ignore: Optional[ShouldIgnoreType],
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
        # by default, ignore the introspection fields which begin
        # with double underscores
        should_ignore_field = is_introspection_key(node.name.value) or (
            should_ignore(
                IgnoreContext(
                    get_field_name(node),
                    get_field_arguments(node),
                    node,
                    context,
                )
            )
            if should_ignore is not None
            else False
        )

        if should_ignore_field or not node.selection_set:
            return 0

        return 1 + max(
            map(
                lambda selection: determine_depth(
                    node=selection,
                    fragments=fragments,
                    depth_so_far=depth_so_far + 1,
                    max_depth=max_depth,
                    context=context,
                    operation_name=operation_name,
                    should_ignore=should_ignore,
                ),
                node.selection_set.selections,
            )
        )
    elif isinstance(node, FragmentSpreadNode):
        return determine_depth(
            node=fragments[node.name.value],
            fragments=fragments,
            depth_so_far=depth_so_far,
            max_depth=max_depth,
            context=context,
            operation_name=operation_name,
            should_ignore=should_ignore,
        )
    elif isinstance(
        node, (InlineFragmentNode, FragmentDefinitionNode, OperationDefinitionNode)
    ):
        return max(
            map(
                lambda selection: determine_depth(
                    node=selection,
                    fragments=fragments,
                    depth_so_far=depth_so_far,
                    max_depth=max_depth,
                    context=context,
                    operation_name=operation_name,
                    should_ignore=should_ignore,
                ),
                node.selection_set.selections,
            )
        )
    else:
        raise TypeError(f"Depth crawler cannot handle: {node.kind}")  # pragma: no cover


def create_validator_deprecated(
    max_depth: int,
    ignore: Optional[List[IgnoreType]] = None,
    callback: Optional[Callable[[Dict[str, int]], None]] = None,
) -> Type[ValidationRule]:
    class DepthLimitValidator(ValidationRule):
        def __init__(self, validation_context: ValidationContext):
            document = validation_context.document
            definitions = document.definitions

            fragments = get_fragments(definitions)
            queries = get_queries_and_mutations(definitions)
            query_depths = {}

            for name in queries:
                query_depths[name] = determine_depth_deprecated(
                    node=queries[name],
                    fragments=fragments,
                    depth_so_far=0,
                    max_depth=max_depth,
                    context=validation_context,
                    operation_name=name,
                    ignore=ignore,
                )

            if callable(callback):
                callback(query_depths)
            super().__init__(validation_context)

    return DepthLimitValidator


def determine_depth_deprecated(
    node: Node,
    fragments: Dict[str, FragmentDefinitionNode],
    depth_so_far: int,
    max_depth: int,
    context: ValidationContext,
    operation_name: str,
    ignore: Optional[List[IgnoreType]] = None,
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
        # by default, ignore the introspection fields which begin
        # with double underscores
        should_ignore = is_introspection_key(node.name.value) or is_ignored(
            node, ignore
        )

        if should_ignore or not node.selection_set:
            return 0

        return 1 + max(
            map(
                lambda selection: determine_depth_deprecated(
                    node=selection,
                    fragments=fragments,
                    depth_so_far=depth_so_far + 1,
                    max_depth=max_depth,
                    context=context,
                    operation_name=operation_name,
                    ignore=ignore,
                ),
                node.selection_set.selections,
            )
        )
    elif isinstance(node, FragmentSpreadNode):
        return determine_depth_deprecated(
            node=fragments[node.name.value],
            fragments=fragments,
            depth_so_far=depth_so_far,
            max_depth=max_depth,
            context=context,
            operation_name=operation_name,
            ignore=ignore,
        )
    elif isinstance(
        node, (InlineFragmentNode, FragmentDefinitionNode, OperationDefinitionNode)
    ):
        return max(
            map(
                lambda selection: determine_depth_deprecated(
                    node=selection,
                    fragments=fragments,
                    depth_so_far=depth_so_far,
                    max_depth=max_depth,
                    context=context,
                    operation_name=operation_name,
                    ignore=ignore,
                ),
                node.selection_set.selections,
            )
        )
    else:
        raise TypeError(f"Depth crawler cannot handle: {node.kind}")  # pragma: no cover


def is_ignored(node: FieldNode, ignore: Optional[List[IgnoreType]] = None) -> bool:
    if ignore is None:
        return False

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
            raise TypeError(f"Invalid ignore option: {rule}")

    return False
