from __future__ import annotations

import dataclasses
import sys
from typing import Any, Dict, List, Type

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    FieldWithResolverAndDefaultFactoryError,
    FieldWithResolverAndDefaultValueError,
    PrivateStrawberryFieldError,
)
from strawberry.types.base import has_object_definition
from strawberry.types.field import StrawberryField
from strawberry.types.private import is_private
from strawberry.types.unset import UNSET


def _get_fields(
    cls: Type[Any], original_type_annotations: Dict[str, Type[Any]]
) -> List[StrawberryField]:
    """Get all the strawberry fields off a strawberry.type cls.

    This function returns a list of StrawberryFields (one for each field item), while
    also paying attention the name and typing of the field.

    StrawberryFields can be defined on a strawberry.type class as either a dataclass-
    style field or using strawberry.field as a decorator.

    ```python
    import strawberry


    @strawberry.type
    class Query:
        type_1a: int = 5
        type_1b: int = strawberry.field(...)
        type_1c: int = strawberry.field(resolver=...)

        @strawberry.field
        def type_2(self) -> int: ...
    ```

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
    fields: Dict[str, StrawberryField] = {}

    # before trying to find any fields, let's first add the fields defined in
    # parent classes, we do this by checking if parents have a type definition
    for base in cls.__bases__:
        if has_object_definition(base):
            base_fields = {
                field.python_name: field
                for field in base.__strawberry_definition__.fields
            }

            # Add base's fields to cls' fields
            fields = {**fields, **base_fields}

    # Find the class the each field was originally defined on so we can use
    # that scope later when resolving the type, as it may have different names
    # available to it.
    origins: Dict[str, type] = {field_name: cls for field_name in cls.__annotations__}

    for base in cls.__mro__:
        if has_object_definition(base):
            for field in base.__strawberry_definition__.fields:
                if field.python_name in base.__annotations__:
                    origins.setdefault(field.name, base)

    # then we can proceed with finding the fields for the current class
    for field in dataclasses.fields(cls):  # type: ignore
        if isinstance(field, StrawberryField):
            # Check that the field type is not Private
            if is_private(field.type):
                raise PrivateStrawberryFieldError(field.python_name, cls)

            # Check that default is not set if a resolver is defined
            if (
                field.default is not dataclasses.MISSING
                and field.default is not UNSET
                and field.base_resolver is not None
            ):
                raise FieldWithResolverAndDefaultValueError(
                    field.python_name, cls.__name__
                )

            # Check that default_factory is not set if a resolver is defined
            # Note: using getattr because of this issue:
            # https://github.com/python/mypy/issues/6910
            default_factory = getattr(field, "default_factory", None)
            if (
                default_factory is not dataclasses.MISSING
                and default_factory is not UNSET
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

            # Set the correct namespace for annotations if a namespace isn't
            # already set
            # Note: We do this here rather in the `Strawberry.type` setter
            # function because at that point we don't have a link to the object
            # type that the field as attached to.
            if (
                isinstance(field.type_annotation, StrawberryAnnotation)
                and field.type_annotation.namespace is None
            ):
                field.type_annotation.set_namespace_from_field(field)

        # Create a StrawberryField for fields that didn't use strawberry.field
        else:
            # Only ignore Private fields that weren't defined using StrawberryFields
            if is_private(field.type):
                continue

            origin = origins.get(field.name, cls)
            module = sys.modules[origin.__module__]

            # Create a StrawberryField, for fields of Types #1 and #2a
            field = StrawberryField(  # noqa: PLW2901
                python_name=field.name,
                graphql_name=None,
                type_annotation=StrawberryAnnotation(
                    annotation=field.type,
                    namespace=module.__dict__,
                ),
                origin=origin,
                default=getattr(cls, field.name, dataclasses.MISSING),
            )

        field_name = field.python_name

        assert_message = "Field must have a name by the time the schema is generated"
        assert field_name is not None, assert_message

        if field.name in original_type_annotations:
            field.type = original_type_annotations[field.name]
            field.type_annotation = StrawberryAnnotation(annotation=field.type)

        # TODO: Raise exception if field_name already in fields
        fields[field_name] = field

    return list(fields.values())


__all__ = ["_get_fields"]
