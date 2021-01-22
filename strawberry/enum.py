import dataclasses
from enum import EnumMeta
from typing import Any, Callable, List, Optional, Union

from .exceptions import NotAnEnum


@dataclasses.dataclass
class EnumValue:
    name: str
    value: Any


@dataclasses.dataclass
class EnumDefinition:
    name: str
    values: List[EnumValue]
    description: Optional[str]


def _process_enum(
    cls: EnumMeta, name: Optional[str] = None, description: Optional[str] = None
) -> EnumMeta:
    if not isinstance(cls, EnumMeta):
        raise NotAnEnum()

    if not name:
        name = cls.__name__

    description = description

    values = [EnumValue(item.name, item.value) for item in cls]  # type: ignore

    cls._enum_definition = EnumDefinition(  # type: ignore
        name=name,
        values=values,
        description=description,
    )

    return cls


def enum(
    _cls: EnumMeta = None, *, name=None, description=None
) -> Union[EnumMeta, Callable[[EnumMeta], EnumMeta]]:
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """

    def wrap(cls: EnumMeta) -> EnumMeta:
        return _process_enum(cls, name, description)

    if not _cls:
        return wrap

    return wrap(_cls)
