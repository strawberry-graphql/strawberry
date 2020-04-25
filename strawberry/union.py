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
        if not hasattr(self, "field"):
            raise WrongReturnTypeForUnion(value.field_name, str(type(self)))

        if self.field not in _type.types:
            raise UnallowedReturnTypeForUnion(
                value.field_name, str(type(self)), _type.types
            )

        return self.field

    # TODO: union types don't work with scalar types
    # so we want to return a nice error
    # also we want to make sure we have been passed
    # strawberry types
    field = GraphQLUnionType(name, [type.field for type in types])
    field.resolve_type = _resolve_type
    # HACK !!!1
    field.field = field

    return field
