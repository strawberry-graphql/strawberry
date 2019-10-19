from typing import NewType

from graphql.type.scalars import GraphQLScalarType

from .type_converter import REGISTRY


def _process_scalar(cls, *, serialize):
    name = cls.__name__

    custom_scalar_type = NewType(name, cls)

    REGISTRY[custom_scalar_type] = GraphQLScalarType(name=name, serialize=serialize)

    return custom_scalar_type


def scalar(cls=None, *, serialize):
    def wrap(cls):
        return _process_scalar(cls, serialize=serialize)

    if cls is None:
        return wrap

    return wrap(cls)
