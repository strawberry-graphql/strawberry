from enum import Enum
from typing import Optional, Type

from strawberry.types import StrawberryType


class StrawberryEnum(StrawberryType):
    def __init__(self, cls: Optional[Type[Enum]] = None, *,
                 name: Optional[str] = None, description: Optional[str] = None):
        self.wrapped_enum = cls
        self._name = name
        self._description = description

    def __call__(self, cls: Type[Enum]):
        self.wrapped_enum = cls

    @property
    def type(self) -> ...:
        # TODO: What would this be?
        ...

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def description(self) -> Optional[str]:
        return self._description


def enum(cls: Optional[Type[Enum]] = None, *, name: Optional[str] = None,
         description: Optional[str] = None) -> StrawberryEnum:
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """
    return StrawberryEnum(
        cls=cls,
        name=name,
        description=description
    )
