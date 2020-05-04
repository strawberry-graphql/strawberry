import typing

from graphql import GraphQLUnionType

from .exceptions import UnallowedReturnTypeForUnion, WrongReturnTypeForUnion
from .utils.typing import is_generic, is_type_var


def _find_type_for_generic_union(root):
    # might need to preserve ordering (typing.Generic[T, V] vs typing.Generic[V, T])
    type_var_fields = [
        field_name
        for field_name, field_type in root.__annotations__.items()
        if is_type_var(field_type)
    ]

    types = tuple(type(getattr(root, field)) for field in type_var_fields)

    return root._copies[types]


def union(name: str, types: typing.Tuple[typing.Type], *, description=None):
    """Creates a new named Union type.

    Example usages:

    >>> strawberry.union(
    >>>     "Name",
    >>>     (A, B),
    >>> )

    >>> strawberry.union(
    >>>     "Name",
    >>>     (A, B),
    >>> )
    """

    from .type_converter import get_graphql_type_for_annotation

    def _resolve_type(root, info, _type):
        if not hasattr(root, "graphql_type"):
            raise WrongReturnTypeForUnion(info.field_name, str(type(root)))

        if is_generic(type(root)):
            return _find_type_for_generic_union(root)

        if root.graphql_type not in _type.types:
            raise UnallowedReturnTypeForUnion(
                info.field_name, str(type(root)), _type.types
            )

        return root.graphql_type

    # TODO: union types don't work with scalar types
    # so we want to return a nice error
    # also we want to make sure we have been passed
    # strawberry types
    graphql_type = GraphQLUnionType(
        name,
        [
            get_graphql_type_for_annotation(type, name, force_optional=True)
            for type in types
        ],
    )
    graphql_type.resolve_type = _resolve_type

    class X:
        def __init__(self, graphql_type):
            self.graphql_type = graphql_type

    return X(graphql_type)
