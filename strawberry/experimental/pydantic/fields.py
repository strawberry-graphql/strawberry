import builtins
from types import UnionType as TypingUnionType
from typing import Annotated, Any
from typing import GenericAlias as TypingGenericAlias  # type: ignore

from pydantic import BaseModel

from strawberry.experimental.pydantic._compat import (
    PydanticCompat,
    get_args,
    get_origin,
    lenient_issubclass,
)
from strawberry.experimental.pydantic.exceptions import (
    UnregisteredTypeException,
)
from strawberry.types.base import StrawberryObjectDefinition


def replace_pydantic_types(type_: Any, is_input: bool) -> Any:
    if lenient_issubclass(type_, BaseModel):
        attr = "_strawberry_input_type" if is_input else "_strawberry_type"
        if hasattr(type_, attr):
            return getattr(type_, attr)
        raise UnregisteredTypeException(type_)
    return type_


def replace_types_recursively(
    type_: Any, is_input: bool, compat: PydanticCompat
) -> Any:
    """Runs the conversions recursively into the arguments of generic types if any."""
    basic_type = compat.get_basic_type(type_)
    replaced_type = replace_pydantic_types(basic_type, is_input)

    origin = get_origin(type_)

    # Fast path: not a generic/union or doesn't have type args
    if not origin or not hasattr(type_, "__args__"):
        return replaced_type

    # Fetch the args from replaced_type so that nested replaced objects/types are correct
    orig_args = get_args(replaced_type)
    converted = tuple(
        replace_types_recursively(t, is_input=is_input, compat=compat)
        for t in orig_args
    )

    # Avoid recreating identical generic/union/annotated types when possible
    if converted == orig_args:
        return replaced_type

    if isinstance(replaced_type, TypingGenericAlias):
        return TypingGenericAlias(origin, converted)
    if isinstance(replaced_type, TypingUnionType):
        return converted

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
