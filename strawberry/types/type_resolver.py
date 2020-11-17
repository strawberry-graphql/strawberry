import dataclasses
import sys
from typing import Dict, List, Optional, Type, Union, cast

from strawberry.exceptions import (
    MissingTypesForGenericError,
    PrivateStrawberryFieldError,
)
from strawberry.lazy_type import LazyType
from strawberry.private import Private
from strawberry.union import StrawberryUnion, union
from strawberry.utils.str_converters import to_camel_case
from strawberry.utils.typing import (
    get_args,
    get_async_generator_annotation,
    get_list_annotation,
    get_optional_annotation,
    get_parameters,
    has_type_var,
    is_async_generator,
    is_forward_ref,
    is_list,
    is_optional,
    is_type_var,
    is_union,
)

from .generics import copy_type_with, get_name_from_types
from .types import ArgumentDefinition, FieldDefinition, undefined


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


def resolve_type(field_definition: Union[FieldDefinition, ArgumentDefinition]) -> None:
    # convert a python type to include a strawberry definition, so for example
    # Union becomes a class with a UnionDefinition, Generics become an actual
    # type definition. This helps with making the code to convert the type definitions
    # to GraphQL types, as we only have to deal with Python's typings in one place.

    type = cast(Type, field_definition.type)
    origin_name = cast(str, field_definition.origin_name)

    if isinstance(type, str):
        module = sys.modules[field_definition.origin.__module__].__dict__

        type = eval(type, module)
        field_definition.type = type

    if isinstance(type, LazyType):
        field_definition.type = type.resolve_type()
        type = cast(Type, field_definition.type)

    if is_forward_ref(type):
        # if the type is a forward reference we try to resolve the type by
        # finding it in the global namespace of the module where the field
        # was initially declared. This will break when the type is not declared
        # in the main scope, but we don't want to support that use case
        # see https://mail.python.org/archives/list/typing-sig@python.org/thread/SNKJB2U5S74TWGDWVD6FMXOP63WVIGDR/  # noqa: E501

        type_name = type.__forward_arg__

        module = sys.modules[field_definition.origin.__module__]

        # TODO: we should probably raise an error if we can't find the type
        type = module.__dict__[type_name]

        field_definition.type = type

        return

    if is_async_generator(type):
        # TODO: shall we raise a warning if field is not used in a subscription?

        # async generators are used in subscription, we only need the yield type
        # https://docs.python.org/3/library/typing.html#typing.AsyncGenerator
        field_definition.type = get_async_generator_annotation(type)

        return resolve_type(field_definition)

    # check for Optional[A] which is represented as Union[A, None], we
    # have an additional check for proper unions below
    if is_optional(type) and len(type.__args__) == 2:
        # this logics works around List of optionals and Optional lists of Optionals:
        # >>> Optional[List[Str]]
        # >>> Optional[List[Optional[Str]]]
        # the field is only optional if it is not a list or if it was already optional
        # since we mark the child as optional when the field is a list

        field_definition.is_optional = (
            True and not field_definition.is_list or field_definition.is_optional
        )
        field_definition.is_child_optional = field_definition.is_list
        field_definition.type = get_optional_annotation(type)

        return resolve_type(field_definition)

    elif is_list(type):
        # TODO: maybe this should be an argument definition when it is argument
        # but doesn't matter much
        child_definition = FieldDefinition(
            origin=field_definition.origin,  # type: ignore
            name=None,
            origin_name=None,
            type=get_list_annotation(type),
        )

        resolve_type(child_definition)

        field_definition.type = None
        field_definition.is_list = True
        field_definition.child = child_definition

        return

    # case for Union[A, B, C], it also handles Optional[Union[A, B, C]] as optionals
    # type hints are represented as Union[..., None].

    elif is_union(type):
        # Optional[Union[A, B]] is represented as Union[A, B, None] so we need
        # too check again if the field is optional as the check above only checks
        # for single Optionals
        field_definition.is_optional = is_optional(type)

        types = type.__args__

        # we use a simplified version of resolve_type since unions in GraphQL
        # are simpler and cannot contain lists or optionals

        types = tuple(
            _resolve_generic_type(t, origin_name)
            for t in types
            if t is not None.__class__
        )

        field_definition.is_union = True
        field_definition.type = union(get_name_from_types(types), types)

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
            name = cast(str, field_definition.origin_name)

            raise MissingTypesForGenericError(name, type)

        # we only make a copy when all the arguments are not type vars
        if not all(is_type_var(a) for a in args):
            field_definition.type = copy_type_with(type, *args)

    if isinstance(type, StrawberryUnion):
        field_definition.is_union = True


def _get_type_params_for_field(
    field_definition: FieldDefinition,
) -> Optional[List[Type]]:
    if field_definition.is_list:
        child = cast(FieldDefinition, field_definition.child)

        return _get_type_params_for_field(child)

    type = cast(Type, field_definition.type)

    if isinstance(type, StrawberryUnion):
        types = type.types
        type_vars = [t for t in types if is_type_var(t)]

        if type_vars:
            return type_vars

    if is_type_var(type):
        return [type]

    if has_type_var(type):
        return get_parameters(type)

    return None


def _get_type_params(fields: List[FieldDefinition]) -> Dict[str, Type]:
    type_params = {}

    for field in fields:
        name = cast(str, field.origin_name)
        params = _get_type_params_for_field(field)

        # TODO: support multiple
        if params:
            type_params[name] = params[0]

    return type_params


def _resolve_types(fields: List[FieldDefinition]) -> List[FieldDefinition]:
    for field in fields:
        resolve_type(field)

    return fields


def _get_fields(cls: Type) -> List[FieldDefinition]:
    """Get all the strawberry field definitions off a strawberry.type cls

    This function returns a list of FieldDefinitions (one for each field item), while
    also paying attention the name and typing of the field.

    Strawberry fields can be defined on a strawberry.type class as either a dataclass-
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
        A pure dataclass-style field. Will not have a FieldDefinition; one will
        need to be created in this function. Type annotation is required.

    Type #2:
        A field defined using @strawberry.field as a decorator around the
        resolver. The resolver must be type-annotated.

    The FieldDefinition.name value will be assigned to the field's name on the class if
    one is not set by either using an explicit strawberry.field(name=...) or by passing
    a named function (i.e. not an anonymous lambda) to strawberry.field (typically as a
    decorator).
    """
    field_definitions: Dict[str, FieldDefinition] = {}

    # before trying to find any fields, let's first add the fields defined in
    # parent classes, we do this by checking if parents have a type definition
    for base in cls.__bases__:
        if hasattr(base, "_type_definition"):
            base_field_definitions = {
                field.origin_name: field
                # TODO: we need to rename _fields to something else
                for field in base._type_definition._fields  # type: ignore
            }

            # Add base's field definitions to cls' field definitions
            field_definitions = {**field_definitions, **base_field_definitions}

    # Deferred import to avoid import cycles
    from strawberry.field import StrawberryField

    # then we can proceed with finding the fields for the current class
    for field in dataclasses.fields(cls):

        if isinstance(field, StrawberryField):
            # Use the existing FieldDefinition
            field_definition = field._field_definition

            # Check that the field type is not Private
            if isinstance(field_definition.type, Private):
                raise PrivateStrawberryFieldError(field.name, cls.__name__)

            # we make sure that the origin is either the field's resolver when
            # called as:
            #
            # >>> @strawberry.field
            # ... def x(self): ...
            #
            # or the class where this field was defined, so we always have
            # the correct origin for determining field types when resolving
            # the types.
            field_definition.origin = field_definition.origin or cls

        # Create a FieldDefinition for fields that didn't use strawberry.field
        else:
            # Only ignore Private fields that weren't defined using StrawberryFields
            if isinstance(field.type, Private):
                continue

            # Create a FieldDefinition, for fields of Types #1 and #2a
            field_definition = FieldDefinition(
                origin_name=field.name,
                name=to_camel_case(field.name),
                type=field.type,
                origin=cls,
                default_value=getattr(cls, field.name, undefined),
            )

        field_name = field_definition.origin_name

        assert_message = "Field must have a name by the time the schema is generated"
        assert field_name is not None, assert_message

        field_definitions[field_name] = field_definition

    return list(field_definitions.values())
