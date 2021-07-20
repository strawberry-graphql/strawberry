import typing
from collections.abc import AsyncGenerator
from typing import Type, TypeVar


def is_list(annotation: Type) -> bool:
    """Returns True if annotation is a List"""

    annotation_origin = getattr(annotation, "__origin__", None)

    return annotation_origin == list


def is_union(annotation: Type) -> bool:
    """Returns True if annotation is a Union"""

    annotation_origin = getattr(annotation, "__origin__", None)

    return annotation_origin == typing.Union


def is_optional(annotation: Type) -> bool:
    """Returns True if the annotation is Optional[SomeType]"""

    # Optionals are represented as unions

    if not is_union(annotation):
        return False

    types = annotation.__args__

    # A Union to be optional needs to have at least one None type
    return any([x == None.__class__ for x in types])  # noqa:E711


def get_optional_annotation(annotation: Type) -> Type:
    types = annotation.__args__

    non_none_types = tuple(x for x in types if x != None.__class__)  # noqa:E711

    # if we have multiple non none types we want to return a copy of this
    # type (normally a Union type).

    if len(non_none_types) > 1:
        return annotation.copy_with(non_none_types)

    return non_none_types[0]


def get_list_annotation(annotation: Type) -> Type:
    return annotation.__args__[0]


def is_concrete_generic(annotation: type) -> bool:
    ignored_generics = (list, tuple, typing.Union, typing.ClassVar, AsyncGenerator)
    return (
        isinstance(annotation, typing._GenericAlias)  # type:ignore
        and annotation.__origin__ not in ignored_generics
    )


def is_generic_subclass(annotation: type) -> bool:
    return isinstance(annotation, type) and issubclass(
        annotation, typing.Generic  # type:ignore
    )


def is_generic(annotation: type) -> bool:
    """Returns True if the annotation is or extends a generic."""

    return (
        # TODO: These two lines appear to have the same effect. When will an
        #       annotation have parameters but not satisfy the first condition?
        (is_generic_subclass(annotation) or is_concrete_generic(annotation))
        and bool(get_parameters(annotation))
    )


def is_type_var(annotation: Type) -> bool:
    """Returns True if the annotation is a TypeVar."""

    return isinstance(annotation, TypeVar)  # type:ignore


def get_parameters(annotation: Type):
    if (
        isinstance(annotation, typing._GenericAlias)  # type:ignore
        or isinstance(annotation, type)
        and issubclass(annotation, typing.Generic)  # type:ignore
        and annotation is not typing.Generic
    ):
        return annotation.__parameters__
    else:
        return ()  # pragma: no cover
