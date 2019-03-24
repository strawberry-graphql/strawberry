import typing
from functools import partial

from dataclasses import dataclass
from graphql import (
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLObjectType,
)
from graphql.utilities.schema_printer import print_type

from .constants import IS_STRAWBERRY_FIELD, IS_STRAWBERRY_INPUT
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


def type(cls, *, is_input=False):
    def wrap():
        name = cls.__name__
        REGISTRY[name] = cls

        def repr_(self):
            return print_type(self.field)

        setattr(cls, "__repr__", repr_)

        annotations = typing.get_type_hints(cls, None, REGISTRY)

        def _get_fields():
            FieldClass = GraphQLInputField if is_input else GraphQLField

            fields = {
                key: FieldClass(
                    get_graphql_type_for_annotation(value, key),
                    **({} if is_input else {"resolve": _get_resolver(cls, key)})
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

        if is_input:
            cls.field = GraphQLInputObjectType(name, lambda: _get_fields())
            setattr(cls, IS_STRAWBERRY_INPUT, True)
        else:
            cls.field = GraphQLObjectType(name, lambda: _get_fields())

        return dataclass(cls, repr=False)

    return wrap()


input = partial(type, is_input=True)
