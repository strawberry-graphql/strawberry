import dataclasses
import sys
import typing
from typing import Dict, List, Type, cast

from strawberry.exceptions import (
    MissingTypesForGenericError,
    PrivateStrawberryFieldError,
)
from strawberry.field import StrawberryField
from strawberry.lazy_type import LazyType
from strawberry.private import Private
from strawberry.union import StrawberryUnion, union
from strawberry.utils.str_converters import to_camel_case
from strawberry.utils.typing import (
    get_args,
    get_async_generator_annotation,
    get_list_annotation,
    get_optional_annotation,
    is_async_generator,
    is_forward_ref,
    is_list,
    is_optional,
    is_type_var,
    is_union,
)

from ..arguments import StrawberryArgument
from .generics import copy_type_with, get_name_from_types

# TODO: why do we have undefined?
from .types import undefined


def _resolve_generic_type(type: Type, field_name: str) -> Type:
    if hasattr(type, "_type_definition") and type._type_definition.is_generic:
        args = get_args(type)

        # raise an error when using generics without passing any type parameter, ie:
        # >>> class X(Generic[T]): ...
        # >>> a: X
        # instead of
        # >>> a: X[str]

        if len(args) == 0:
            raise MissingTypesForGenericError(field_name, type)

        # we only make a copy when all the arguments are not type vars
        if not all(is_type_var(a) for a in args):
            return copy_type_with(type, *args)

    return type


def resolve_type_field(field: StrawberryField) -> None:
    # TODO: This should be handled by StrawberryType in the future
    if isinstance(field.type, str):
        module = sys.modules[field.origin.__module__]

        field.type = eval(field.type, module.__dict__)

    if isinstance(field.type, LazyType):
        field.type = field.type.resolve_type()

    if is_forward_ref(field.type):
        # if the type is a forward reference we try to resolve the type by
        # finding it in the global namespace of the module where the field
        # was initially declared. This will break when the type is not declared
        # in the main scope, but we don't want to support that use case
        # see https://mail.python.org/archives/list/typing-sig@python.org/thread/SNKJB2U5S74TWGDWVD6FMXOP63WVIGDR/  # noqa: E501

        type_name = field.type.__forward_arg__

        module = sys.modules[field.origin.__module__]

        # TODO: we should probably raise an error if we can't find the type
        field.type = module.__dict__[type_name]

        return

    if is_async_generator(field.type):
        # TODO: shall we raise a warning if field is not used in a subscription?

        # async generators are used in subscription, we only need the yield type
        # https://docs.python.org/3/library/typing.html#typing.AsyncGenerator
        field.type = get_async_generator_annotation(field.type)

        return resolve_type_field(field)

    # check for Optional[A] which is represented as Union[A, None], we
    # have an additional check for proper unions below
    if is_optional(field.type) and len(field.type.__args__) == 2:
        # this logics works around List of optionals and Optional lists of Optionals:
        # >>> Optional[List[Str]]
        # >>> Optional[List[Optional[Str]]]
        # the field is only optional if it is not a list or if it was already optional
        # since we mark the child as optional when the field is a list

        field.is_optional = True and not field.is_list or field.is_optional
        field.is_child_optional = field.is_list

        field.type = get_optional_annotation(field.type)

        return resolve_type_field(field)

    elif is_list(field.type):
        child_field = StrawberryField(
            python_name=None,
            graphql_name=None,
            origin=field.origin,  # type: ignore
            type_=get_list_annotation(field.type),
        )
        resolve_type_field(child_field)

        field.is_list = True
        field.child = child_field

        # TODO: Fix StrawberryField.type typing
        field.type = typing.cast(type, None)

        return

    # case for Union[A, B, C], it also handles Optional[Union[A, B, C]] as optionals
    # type hints are represented as Union[..., None].

    elif is_union(field.type):
        # Optional[Union[A, B]] is represented as Union[A, B, None] so we need
        # too check again if the field is optional as the check above only checks
        # for single Optionals
        field.is_optional = is_optional(field.type)

        types = field.type.__args__

        # we use a simplified version of resolve_type since unions in GraphQL
        # are simpler and cannot contain lists or optionals

        types = tuple(
            _resolve_generic_type(t, field.python_name)
            for t in types
            if t is not None.__class__
        )

        field.is_union = True

        # TODO: Fix StrawberryField.type typing
        strawberry_union = typing.cast(type, union(get_name_from_types(types), types))

        field.type = strawberry_union

    # case for Type[A], we want to convert generics to have the concrete types
    # when we pass them, so that we don't have to deal with generics when
    # generating the GraphQL types later on.

    elif (
        hasattr(field.type, "_type_definition")
        and field.type._type_definition.is_generic
    ):
        args = get_args(field.type)

        # raise an error when using generics without passing any type parameter, ie:
        # >>> class X(Generic[T]): ...
        # >>> a: X
        # instead of
        # >>> a: X[str]

        if len(args) == 0:
            raise MissingTypesForGenericError(field.python_name, field.type)

        # we only make a copy when all the arguments are not type vars
        if not all(is_type_var(a) for a in args):
            field.type = copy_type_with(field.type, *args)

    if isinstance(field.type, StrawberryUnion):
        field.is_union = True


def _resolve_type(argument: StrawberryArgument) -> None:
    # TODO: This should be handled by StrawberryType in the future
    # Convert a python type to include a strawberry definition, so for example
    # Union becomes a class with a UnionDefinition, Generics become an actual
    # type definition. This helps with making the code to convert the type definitions
    # to GraphQL types, as we only have to deal with Python's typings in one place.

    type = cast(Type, argument.type)
    assert argument.python_name

    if isinstance(type, str):
        module = sys.modules[argument.origin.__module__].__dict__

        type = eval(type, module)
        argument.type = type

    if isinstance(type, LazyType):
        argument.type = type.resolve_type()
        type = cast(Type, argument.type)

    if is_forward_ref(type):
        # if the type is a forward reference we try to resolve the type by
        # finding it in the global namespace of the module where the field
        # was initially declared. This will break when the type is not declared
        # in the main scope, but we don't want to support that use case
        # see https://mail.python.org/archives/list/typing-sig@python.org/thread/SNKJB2U5S74TWGDWVD6FMXOP63WVIGDR/  # noqa: E501

        type_name = type.__forward_arg__

        module = sys.modules[argument.origin.__module__]

        # TODO: we should probably raise an error if we can't find the type
        type = module.__dict__[type_name]

        argument.type = type

        return

    if is_async_generator(type):
        # TODO: shall we raise a warning if field is not used in a subscription?

        # async generators are used in subscription, we only need the yield type
        # https://docs.python.org/3/library/typing.html#typing.AsyncGenerator
        argument.type = get_async_generator_annotation(type)

        return _resolve_type(argument)

    # check for Optional[A] which is represented as Union[A, None], we
    # have an additional check for proper unions below
    if is_optional(type) and len(type.__args__) == 2:
        # this logics works around List of optionals and Optional lists of Optionals:
        # >>> Optional[List[Str]]
        # >>> Optional[List[Optional[Str]]]
        # the field is only optional if it is not a list or if it was already optional
        # since we mark the child as optional when the field is a list

        argument.is_optional = True and not argument.is_list or argument.is_optional
        argument.is_child_optional = argument.is_list
        argument.type = get_optional_annotation(type)

        return _resolve_type(argument)

    elif is_list(type):
        # TODO: maybe this should be an argument definition when it is argument
        # but doesn't matter much
        child_field = StrawberryField(
            python_name=None,
            graphql_name=None,
            origin=argument.origin,  # type: ignore
            type_=get_list_annotation(type),
        )
        resolve_type_field(child_field)

        argument.type = None
        argument.is_list = True
        argument.child = cast(StrawberryArgument, child_field)

        return

    # case for Union[A, B, C], it also handles Optional[Union[A, B, C]] as optionals
    # type hints are represented as Union[..., None].
    elif is_union(type):
        # Optional[Union[A, B]] is represented as Union[A, B, None] so we need
        # too check again if the field is optional as the check above only checks
        # for single Optionals
        argument.is_optional = is_optional(type)

        types = type.__args__

        # we use a simplified version of resolve_type since unions in GraphQL
        # are simpler and cannot contain lists or optionals

        types = tuple(
            _resolve_generic_type(t, argument.python_name)
            for t in types
            if t is not None.__class__
        )

        argument.is_union = True
        argument.type = union(get_name_from_types(types), types)

    # case for Type[A], we want to convert generics to have the concrete types
    # when we pass them, so that we don't have to deal with generics when
    # generating the GraphQL types later on.

    elif hasattr(type, "_type_definition") and type._type_definition.is_generic:
        args = get_args(type)

        # raise an error when using generics without passing any type parameter, ie:
        # >>> class X(Generic[T]): ...
        # >>> a: X
        # instead of
        # >>> a: X[str]

        if len(args) == 0:
            assert argument.python_name

            raise MissingTypesForGenericError(argument.python_name, type)

        # we only make a copy when all the arguments are not type vars
        if not all(is_type_var(a) for a in args):
            argument.type = copy_type_with(type, *args)

    if isinstance(type, StrawberryUnion):
        argument.is_union = True


def _get_type_params(fields: List[StrawberryField]) -> Dict[str, Type]:
    type_params = {}

    for field in fields:
        name = field.python_name
        params = field.type_params

        # TODO: support multiple
        if params:
            type_params[name] = params[0]

    return type_params


def _resolve_types(fields: List[StrawberryField]) -> List[StrawberryField]:
    for field in fields:
        resolve_type_field(field)

    return fields


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
                field.graphql_name: field
                # TODO: we need to rename _fields to something else
                for field in base._type_definition._fields  # type: ignore
            }

            # Add base's fields to cls' fields
            fields = {**fields, **base_fields}

    # then we can proceed with finding the fields for the current class
    for field in dataclasses.fields(cls):

        if isinstance(field, StrawberryField):
            # Check that the field type is not Private
            if isinstance(field.type, Private):
                raise PrivateStrawberryFieldError(field.python_name, cls.__name__)

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

        # Create a StrawberryField for fields that didn't use strawberry.field
        else:
            # Only ignore Private fields that weren't defined using StrawberryFields
            if isinstance(field.type, Private):
                continue

            field_type = field.type

            # Create a StrawberryField, for fields of Types #1 and #2a
            field = StrawberryField(
                python_name=field.name,
                graphql_name=to_camel_case(field.name),
                type_=field_type,
                origin=cls,
                default_value=getattr(cls, field.name, undefined),
            )

        field_name = field.graphql_name

        assert_message = "Field must have a name by the time the schema is generated"
        assert field_name is not None, assert_message

        # TODO: Raise exception if field_name already in fields
        fields[field_name] = field

    return list(fields.values())
