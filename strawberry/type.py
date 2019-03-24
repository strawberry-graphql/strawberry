import typing

from dataclasses import dataclass
from graphql import GraphQLField, GraphQLObjectType
from graphql.utilities.schema_printer import print_type

from .constants import IS_STRAWBERRY_FIELD
from .type_converter import REGISTRY, get_graphql_type_for_annotation


def _get_resolver(cls, field_name):
    def _resolver(obj, info):
        # TODO: can we make this nicer?
        # does it work in all the cases?

        field_resolver = getattr(cls(**(obj.__dict__ if obj else {})), field_name)

        if getattr(field_resolver, IS_STRAWBERRY_FIELD, False):
            return field_resolver(obj, info)

        return field_resolver

    return _resolver


def type(cls):
    def wrap():
        name = cls.__name__
        REGISTRY[name] = cls

        def repr_(self):
            return print_type(self.field)

        setattr(cls, "__repr__", repr_)

        annotations = typing.get_type_hints(cls, None, REGISTRY)

        def _get_fields():

            fields = {
                key: GraphQLField(
                    get_graphql_type_for_annotation(value, key),
                    resolve=_get_resolver(cls, key),
                )
                for key, value in annotations.items()
            }

            fields.update(
                {
                    key: value.field
                    for key, value in cls.__dict__.items()
                    if getattr(value, IS_STRAWBERRY_FIELD, False)
                }
            )

            return fields

        cls.field = GraphQLObjectType(name, lambda: _get_fields())

        return dataclass(cls, repr=False)

    return wrap()
