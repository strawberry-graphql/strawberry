import dataclasses
from typing import Any, List, Type

from strawberry.experimental.pydantic.exceptions import UnregisteredTypeException
from strawberry.private import is_private
from strawberry.utils.typing import (
    get_list_annotation,
    get_optional_annotation,
    is_list,
    is_optional,
)


def normalize_type(type_) -> Any:
    if is_list(type_):
        return List[normalize_type(get_list_annotation(type_))]  # type: ignore

    if is_optional(type_):
        return get_optional_annotation(type_)

    return type_


def get_strawberry_type_from_model(type_: Any):
    if hasattr(type_, "_strawberry_type"):
        return type_._strawberry_type
    else:
        raise UnregisteredTypeException(type_)


def get_private_fields(cls: Type) -> List[dataclasses.Field]:
    private_fields: List[dataclasses.Field] = []

    for field in dataclasses.fields(cls):
        if is_private(field.type):
            private_fields.append(field)

    return private_fields
