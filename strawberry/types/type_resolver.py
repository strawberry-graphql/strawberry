import dataclasses
import sys
from typing import Dict, List, Type

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    FieldWithResolverAndDefaultFactoryError,
    FieldWithResolverAndDefaultValueError,
    PrivateStrawberryFieldError,
)
from strawberry.field import StrawberryField
from strawberry.private import is_private

from ..unset import UNSET


def _get_fields(cls: Type) -> List[StrawberryField]:
    """Get all the strawberry fields off a strawberry.type cls

    This function returns a list of StrawberryFields (one for each field item), while
    also paying attention the name and typing of the field.

    StrawberryFields can be defined on a strawberry.type class as either a dataclass-
    style field or using strawberry.field as a decorator.

    >>> import strawberry
    >>> @strawberry.type
    ... class Query:
    ...     type_1a: int = 5
    ...     type_1b: int = strawberry.field(...)
    ...     type_1c: int = strawberry.field(resolver=...)
    ...
    ...     @strawberry.field
    ...     def type_2(self) -> int:
    ...         ...

    Type #1:
        A pure dataclass-style field. Will not have a StrawberryField; one will need to
        be created in this function. Type annotation is required.

    Type #2:
        A field defined using @strawberry.field as a decorator around the resolver. The
        resolver must be type-annotated.

    The StrawberryField.python_name value will be assigned to the field's name on the
    class if one is not set by either using an explicit strawberry.field(name=...) or by
    passing a named function (i.e. not an anonymous lambda) to strawberry.field
    (typically as a decorator).
    """
    # Deferred import to avoid import cycles
    from strawberry.field import StrawberryField

    fields: Dict[str, StrawberryField] = {}

    # before trying to find any fields, let's first add the fields defined in
    # parent classes, we do this by checking if parents have a type definition
    for base in cls.__bases__:
        if hasattr(base, "_type_definition"):
            base_fields = {
                field.python_name: field
                # TODO: we need to rename _fields to something else
                for field in base._type_definition._fields  # type: ignore
            }

            # Add base's fields to cls' fields
            fields = {**fields, **base_fields}

    # Find the class the each field was originally defined on so we can use
    # that scope later when resolving the type, as it may have different names
    # available to it.
    origins: Dict[str, type] = {field_name: cls for field_name in cls.__annotations__}

    for base in cls.__mro__:
        if hasattr(base, "_type_definition"):
            for field in base._type_definition._fields:  # type: ignore
                if field.python_name in base.__annotations__:
                    origins.setdefault(field.name, base)

    # then we can proceed with finding the fields for the current class
    for field in dataclasses.fields(cls):

        if isinstance(field, StrawberryField):
            # Check that the field type is not Private
            if is_private(field.type):
                raise PrivateStrawberryFieldError(field.python_name, cls.__name__)

            # Check that default is not set if a resolver is defined
            if (
                field.default is not dataclasses.MISSING
                and field.base_resolver is not None
            ):
                raise FieldWithResolverAndDefaultValueError(
                    field.python_name, cls.__name__
                )

            # Check that default_factory is not set if a resolver is defined
            # Note: using getattr because of this issue:
            # https://github.com/python/mypy/issues/6910
            if (
                getattr(field, "default_factory") is not dataclasses.MISSING  # noqa
                and field.base_resolver is not None
            ):
                raise FieldWithResolverAndDefaultFactoryError(
                    field.python_name, cls.__name__
                )

            # we make sure that the origin is either the field's resolver when
            # called as:
            #
            # >>> @strawberry.field
            # ... def x(self): ...
            #
            # or the class where this field was defined, so we always have
            # the correct origin for determining field types when resolving
            # the types.
            field.origin = field.origin or cls

            # Make sure types are StrawberryAnnotations
            if not isinstance(field.type_annotation, StrawberryAnnotation):
                module = sys.modules[field.origin.__module__]
                field.type_annotation = StrawberryAnnotation(
                    annotation=field.type_annotation, namespace=module.__dict__
                )

        # Create a StrawberryField for fields that didn't use strawberry.field
        else:
            # Only ignore Private fields that weren't defined using StrawberryFields
            if is_private(field.type):
                continue

            field_type = field.type

            origin = origins.get(field.name, cls)
            module = sys.modules[origin.__module__]

            # Create a StrawberryField, for fields of Types #1 and #2a
            field = StrawberryField(
                python_name=field.name,
                graphql_name=None,
                type_annotation=StrawberryAnnotation(
                    annotation=field_type,
                    namespace=module.__dict__,
                ),
                origin=origin,
                default=getattr(cls, field.name, UNSET),
            )

        field_name = field.python_name

        assert_message = "Field must have a name by the time the schema is generated"
        assert field_name is not None, assert_message

        # TODO: Raise exception if field_name already in fields
        fields[field_name] = field

    return list(fields.values())
