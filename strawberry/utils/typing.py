import typing
from collections.abc import AsyncGenerator, Callable
from typing import Type, TypeVar


try:
    from typing import ForwardRef  # type: ignore
except ImportError:  # pragma: no cover
    # ForwardRef is private in python 3.6 and 3.7
    from typing import _ForwardRef as ForwardRef  # type: ignore


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


def is_async_generator(annotation: Type) -> bool:
    return getattr(annotation, "__origin__", None) == AsyncGenerator


def get_async_generator_annotation(annotation: Type) -> Type:
    return annotation.__args__[0]


def is_generic(annotation: Type) -> bool:
    """Returns True if the annotation is or extends a generic."""
    return (
        isinstance(annotation, type)
        and issubclass(annotation, typing.Generic)  # type:ignore
        or isinstance(annotation, typing._GenericAlias)  # type:ignore
        and annotation.__origin__
        not in (
            list,
            typing.Union,
            tuple,
            typing.ClassVar,
            AsyncGenerator,
        )
    )


def is_type_var(annotation: Type) -> bool:
    """Returns True if the annotation is a TypeVar."""

    return isinstance(annotation, TypeVar)  # type:ignore


def has_type_var(annotation: Type) -> bool:
    """
    Returns True if the annotation or any of
    its argument have a TypeVar as argument.
    """
    return any(
        is_type_var(arg) or has_type_var(arg)
        for arg in getattr(annotation, "__args__", [])
    )


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


def get_origin(annotation: Type):
    if isinstance(annotation, typing._GenericAlias):  # type:ignore
        return (
            annotation.__origin__
            if annotation.__origin__ is not typing.ClassVar
            else None
        )

    if annotation is typing.Generic:  # pragma: no cover
        return typing.Generic

    return None  # pragma: no cover


def get_args(annotation: Type):
    if isinstance(annotation, typing._GenericAlias):  # type:ignore
        res = annotation.__args__

        if (
            get_origin(annotation) is Callable and res[0] is not Ellipsis
        ):  # pragma: no cover
            res = (list(res[:-1]), res[-1])

        return res

    return ()


def is_forward_ref(annotation: Type) -> bool:
    return isinstance(annotation, ForwardRef)
