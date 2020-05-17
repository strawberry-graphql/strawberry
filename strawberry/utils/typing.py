import collections
import typing


def is_list(annotation):
    """Returns True if annotation is a typing.List"""

    annotation_origin = getattr(annotation, "__origin__", None)

    return annotation_origin == list


def is_union(annotation):
    """Returns True if annotation is a typing.Union"""

    annotation_origin = getattr(annotation, "__origin__", None)

    return annotation_origin == typing.Union


def is_optional(annotation):
    """Returns True if the annotation is typing.Optional[SomeType]"""

    # Optionals are represented as unions

    if not is_union(annotation):
        return False

    types = annotation.__args__

    # A Union to be optional needs to have at least one None type
    return any([x == None.__class__ for x in types])  # noqa:E711


def get_optional_annotation(annotation):
    types = annotation.__args__
    non_none_types = [x for x in types if x != None.__class__]  # noqa:E711

    return non_none_types[0]


def get_list_annotation(annotation):
    return annotation.__args__[0]


def is_generic(annotation) -> bool:
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
            collections.abc.AsyncGenerator,
        )
    )


def is_type_var(annotation) -> bool:
    """Returns True if the annotation is a TypeVar."""

    return isinstance(annotation, typing.TypeVar)  # type:ignore


def has_type_var(annotation) -> bool:
    """
    Returns True if the annotation or any of
    its argument have a TypeVar as argument.
    """
    return any(
        is_type_var(arg) or has_type_var(arg)
        for arg in getattr(annotation, "__args__", [])
    )


def get_actual_type(annotation, types_replacement_map):
    """Returns a copy of an annotation by replacing TypeVar"""
    if is_type_var(annotation):
        return types_replacement_map[annotation.__name__]

    if has_type_var(annotation):
        return annotation.copy_with(
            tuple(
                get_actual_type(arg, types_replacement_map)
                for arg in annotation.__args__
            )
        )

    return annotation
