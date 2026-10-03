import builtins
from types import UnionType
from typing import (
    Annotated,
    Any,
    Union,
)
from typing import GenericAlias as TypingGenericAlias  # type: ignore

from strawberry.experimental.pydantic._compat import (
    PydanticCompat,
    get_args,
    get_origin,
    is_model_class,
)
from strawberry.experimental.pydantic.exceptions import (
    UnregisteredTypeException,
)
from strawberry.types.base import StrawberryObjectDefinition


def replace_pydantic_types(type_: Any, is_input: bool) -> Any:
    if is_model_class(type_):
        attr = "_strawberry_input_type" if is_input else "_strawberry_type"
        if hasattr(type_, attr):
            return getattr(type_, attr)
        raise UnregisteredTypeException(type_)
    return type_


def _unwrap_annotated_none(type_: Any) -> Any:
    """Return `None` for union members that are `None` behind an `Annotated`.

    Pydantic lets you annotate the `None` member of a union, for example
    `Union[str, SkipJsonSchema[None]]`. That hides the `NoneType` that tells
    strawberry the field is optional, so the field is read as a union of `str`
    and `Annotated[None, ...]` instead. Metadata on `None` says nothing about
    the GraphQL type, while metadata on any other member can (a
    `strawberry.lazy` reference or a `strawberry.union` name), so only the
    `None` member loses its metadata here.
    """
    if get_origin(type_) is Annotated and get_args(type_)[0] is type(None):
        return type(None)

    return type_


def replace_types_recursively(
    type_: Any, is_input: bool, compat: PydanticCompat
) -> Any:
    """Runs the conversions recursively into the arguments of generic types if any."""
    basic_type = compat.get_basic_type(type_)
    replaced_type = replace_pydantic_types(basic_type, is_input)

    origin = get_origin(type_)

    if not origin or not hasattr(type_, "__args__"):
        return replaced_type

    converted = tuple(
        replace_types_recursively(t, is_input=is_input, compat=compat)
        for t in get_args(replaced_type)
    )

    if isinstance(replaced_type, TypingGenericAlias):
        return TypingGenericAlias(origin, converted)
    if origin is Union or isinstance(replaced_type, UnionType):
        return Union[tuple(_unwrap_annotated_none(t) for t in converted)]  # noqa: UP007

    # TODO: investigate if we could move the check for annotated to the top
    if origin is Annotated and converted:
        converted = (converted[0],)

    replaced_type = replaced_type.copy_with(converted)

    if isinstance(replaced_type, StrawberryObjectDefinition):
        # TODO: Not sure if this is necessary. No coverage in tests
        # TODO: Unnecessary with StrawberryObject
        replaced_type = builtins.type(
            replaced_type.name,
            (),
            {"__strawberry_definition__": replaced_type},
        )

    return replaced_type
