from __future__ import annotations

import base64
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    NewType,
    TypeVar,
    Union,
)

from .custom_scalar import scalar

if TYPE_CHECKING:
    from .custom_scalar import ScalarDefinition, ScalarWrapper

# FIXME: We want to add `default=Any` in the future here, so JSON will be evaluated
# to JSON[Any] instead of JSON[Unknown]. Pyright already supports it, but mypy doesn't
T = TypeVar("T", bound=Any)
ID = NewType("ID", str)


# This is required for mypy/pyright identify JSON[T] as T and not JSON[T]
# They will respect only the typings on `__getitem__` defined in the metaclass
# and ignore `__class_getitem__` on both
class JSONMeta(type):
    def __getitem__(self, item: T) -> T:
        return self.__class_getitem__(item)  # type: ignore


@scalar(
    name="JSON",
    description=(
        "The `JSON` scalar type represents JSON values as specified by "
        "[ECMA-404]"
        "(http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf)."
    ),
    specified_by_url=(
        "http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf"
    ),
    serialize=lambda v: v,
    parse_value=lambda v: v,
)
class JSON(Generic[T], metaclass=JSONMeta):
    ...


Base16 = scalar(
    NewType("Base16", bytes),
    description="Represents binary data as Base16-encoded (hexadecimal) strings.",
    specified_by_url="https://datatracker.ietf.org/doc/html/rfc4648.html#section-8",
    serialize=lambda v: base64.b16encode(v).decode("utf-8"),
    parse_value=lambda v: base64.b16decode(v.encode("utf-8"), casefold=True),
)

Base32 = scalar(
    NewType("Base32", bytes),
    description=(
        "Represents binary data as Base32-encoded strings, using the standard alphabet."
    ),
    specified_by_url=("https://datatracker.ietf.org/doc/html/rfc4648.html#section-6"),
    serialize=lambda v: base64.b32encode(v).decode("utf-8"),
    parse_value=lambda v: base64.b32decode(v.encode("utf-8"), casefold=True),
)

Base64 = scalar(
    NewType("Base64", bytes),
    description=(
        "Represents binary data as Base64-encoded strings, using the standard alphabet."
    ),
    specified_by_url="https://datatracker.ietf.org/doc/html/rfc4648.html#section-4",
    serialize=lambda v: base64.b64encode(v).decode("utf-8"),
    parse_value=lambda v: base64.b64decode(v.encode("utf-8")),
)


def is_scalar(
    annotation: Any,
    scalar_registry: Dict[object, Union[ScalarWrapper, ScalarDefinition]],
) -> bool:
    if annotation in scalar_registry:
        return True

    return hasattr(annotation, "_scalar_definition")
