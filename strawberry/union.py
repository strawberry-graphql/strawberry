import typing

from graphql import GraphQLUnionType

from .exceptions import UnallowedReturnTypeForUnion, WrongReturnTypeForUnion


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

    def _resolve_type(self, value, _type):
        if not hasattr(self, "graphql_type"):
            raise WrongReturnTypeForUnion(value.field_name, str(type(self)))

        if self.graphql_type not in _type.types:
            raise UnallowedReturnTypeForUnion(
                value.field_name, str(type(self)), _type.types
            )

        return self.graphql_type

    # TODO: union types don't work with scalar types
    # so we want to return a nice error
    # also we want to make sure we have been passed
    # strawberry types
    graphql_type = GraphQLUnionType(name, [type.graphql_type for type in types])
    graphql_type.resolve_type = _resolve_type

    class X:
        def __init__(self, graphql_type):
            self.graphql_type = graphql_type

    return X(graphql_type)
