from typing import Optional, Type, TypeVar

from .object import StrawberryObject
from .type import StrawberryType

T = TypeVar("T", bound=StrawberryObject)


class StrawberryArgument(StrawberryType[T]):
    def __init__(self, name: str, type_: Type[T], *,
                 description: Optional[str],
                 # TODO: Can we use None, or do we want fields.NO_DEFAULT_VALUE?
                 default_value: Optional[T] = ...):
        self._name = name
        self._type = type_
        self._description = description
        self._default_value = default_value

    @property
    def name(self) -> str:
        return self._description

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def type(self) -> Type[T]:
        return self._type
