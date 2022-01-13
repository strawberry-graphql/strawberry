import dataclasses
from enum import EnumMeta
from typing import Any, Callable, List, Mapping, Optional, TypeVar, Union, overload

from strawberry.type import StrawberryType

from .exceptions import ObjectIsNotAnEnumError


@dataclasses.dataclass
class EnumValue:
    name: str
    value: Any


@dataclasses.dataclass
class EnumDefinition(StrawberryType):
    wrapped_cls: EnumMeta
    name: str
    values: List[EnumValue]
    description: Optional[str]

    def __hash__(self) -> int:
        # TODO: Is this enough for unique-ness?
        return hash(self.name)

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> Union[StrawberryType, type]:
        return super().copy_with(type_var_map)

    @property
    def is_generic(self) -> bool:
        return False


EnumType = TypeVar("EnumType", bound=EnumMeta)


def _process_enum(
    cls: EnumType, name: Optional[str] = None, description: Optional[str] = None
) -> EnumType:
    if not isinstance(cls, EnumMeta):
        raise ObjectIsNotAnEnumError(cls)

    if not name:
        name = cls.__name__

    description = description

    values = [EnumValue(item.name, item.value) for item in cls]  # type: ignore

    cls._enum_definition = EnumDefinition(  # type: ignore
        wrapped_cls=cls,
        name=name,
        values=values,
        description=description,
    )

    return cls


@overload
def enum(_cls: EnumType, *, name=None, description=None) -> EnumType:
    ...


@overload
def enum(
    _cls: None = None, *, name=None, description=None
) -> Callable[[EnumType], EnumType]:
    ...


def enum(
    _cls: Optional[EnumType] = None, *, name=None, description=None
) -> Union[EnumType, Callable[[EnumType], EnumType]]:
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """

    def wrap(cls: EnumType) -> EnumType:
        return _process_enum(cls, name, description)

    if not _cls:
        return wrap

    return wrap(_cls)
