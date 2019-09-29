from enum import EnumMeta

from graphql import GraphQLEnumType, GraphQLEnumValue

from .exceptions import NotAnEnum
from .type_converter import REGISTRY


def _process_enum(cls, name=None, description=None):
    if not isinstance(cls, EnumMeta):
        raise NotAnEnum()

    if not name:
        name = cls.__name__

    REGISTRY[name] = cls

    description = description or cls.__doc__

    cls.field = GraphQLEnumType(
        name=name,
        values=[(item.name, GraphQLEnumValue(item.value)) for item in cls],
        description=description,
    )

    return cls


def enum(_cls=None, *, name=None, description=None):
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """

    def wrap(cls):
        return _process_enum(cls, name, description)

    if not _cls:
        return wrap

    return wrap(_cls)
