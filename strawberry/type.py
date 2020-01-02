from functools import partial

import dataclasses
from graphql import GraphQLInputObjectType, GraphQLInterfaceType, GraphQLObjectType

from .constants import IS_STRAWBERRY_FIELD, IS_STRAWBERRY_INPUT, IS_STRAWBERRY_INTERFACE
from .field import field, strawberry_field
from .type_converter import REGISTRY
from .utils.str_converters import to_camel_case


def _interface_resolve_type(result, info, return_type):
    """Resolves the correct type for an interface"""
    return result.__class__.field


def _get_resolver(cls, field_name):
    class_field = getattr(cls, field_name, None)

    if class_field and getattr(class_field, "resolver", None):
        return class_field.resolver

    def _resolver(root, info):
        if not root:
            return None

        field_resolver = getattr(root, field_name, None)

        if getattr(field_resolver, IS_STRAWBERRY_FIELD, False):
            return field_resolver(root, info)

        elif field_resolver.__class__ is strawberry_field:
            # TODO: support default values
            return None

        return field_resolver

    return _resolver


def _process_type(cls, *, is_input=False, is_interface=False, description=None):
    name = cls.__name__
    REGISTRY[name] = cls

    def _get_fields(wrapped):
        class_fields = dataclasses.fields(wrapped)

        fields = {}

        for class_field in class_fields:
            field_name = getattr(class_field, "field_name", None) or to_camel_case(
                class_field.name
            )
            description = getattr(class_field, "field_description", None)
            permission_classes = getattr(class_field, "field_permission_classes", None)
            resolver = getattr(class_field, "field_resolver", None) or _get_resolver(
                cls, class_field.name
            )
            resolver.__annotations__["return"] = class_field.type

            fields[field_name] = field(
                resolver,
                is_input=is_input,
                description=description,
                permission_classes=permission_classes,
            ).field

        strawberry_fields = {}

        for base in [cls, *cls.__bases__]:
            strawberry_fields.update(
                {
                    key: value
                    for key, value in base.__dict__.items()
                    if getattr(value, IS_STRAWBERRY_FIELD, False)
                }
            )

        for key, value in strawberry_fields.items():
            name = getattr(value, "field_name", None) or to_camel_case(key)

            fields[name] = value.field

        return fields

    if is_input:
        setattr(cls, IS_STRAWBERRY_INPUT, True)
    elif is_interface:
        setattr(cls, IS_STRAWBERRY_INTERFACE, True)

    extra_kwargs = {"description": description or cls.__doc__}

    wrapped = dataclasses.dataclass(cls)

    if is_input:
        TypeClass = GraphQLInputObjectType
    elif is_interface:
        TypeClass = GraphQLInterfaceType

        # TODO: in future we might want to be able to override this
        # for example to map a class (like a django model) to one
        # type of the interface
        extra_kwargs["resolve_type"] = _interface_resolve_type
    else:
        TypeClass = GraphQLObjectType

        extra_kwargs["interfaces"] = [
            klass.field
            for klass in cls.__bases__
            if hasattr(klass, IS_STRAWBERRY_INTERFACE)
        ]

    wrapped.field = TypeClass(name, lambda: _get_fields(wrapped), **extra_kwargs)

    return wrapped


def type(cls=None, *, is_input=False, is_interface=False, description=None):
    """Annotates a class as a GraphQL type.

    Example usage:

    >>> @strawberry.type:
    >>> class X:
    >>>     field_abc: str = "ABC"
    """

    def wrap(cls):
        return _process_type(
            cls, is_input=is_input, is_interface=is_interface, description=description
        )

    if cls is None:
        return wrap

    return wrap(cls)


input = partial(type, is_input=True)
interface = partial(type, is_interface=True)
