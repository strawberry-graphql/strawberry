import dataclasses
from enum import Enum, EnumMeta
from typing import Any, Callable, Iterable, List, Optional, Union, cast

from .exceptions import NotAnEnum
from .utils.str_converters import to_camel_case


@dataclasses.dataclass
class EnumValue:
    name: str
    value: Any


class StrawberryEnum:
    def __init__(
        self,
        enum: EnumMeta,
        python_name: str,
        graphql_name: Optional[str],
        description: Optional[str],
    ) -> None:
        self.enum = enum
        self.python_name = python_name
        self._graphql_name = graphql_name
        self.description = description

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.enum(*args, **kwds)

    def __getattr__(self, attr):
        if hasattr(self.enum, attr):
            return self.enum[attr]

        return super().__getattribute__(attr)

    @property
    def values(self) -> List[EnumValue]:
        return [
            EnumValue(item.name, item.value) for item in cast(Iterable[Enum], self.enum)
        ]

    @property
    def graphql_name(self) -> str:
        if self._graphql_name:
            return self._graphql_name

        return to_camel_case(self.python_name)


def _process_enum(
    cls: EnumMeta, name: Optional[str] = None, description: Optional[str] = None
) -> StrawberryEnum:
    if not isinstance(cls, EnumMeta):
        raise NotAnEnum()

    if not name:
        name = cls.__name__

    return StrawberryEnum(
        enum=cls,
        python_name=cls.__name__,
        graphql_name=name,
        description=description,
    )


def enum(
    _cls: EnumMeta = None, *, name=None, description=None
) -> Union[StrawberryEnum, Callable[[EnumMeta], StrawberryEnum]]:
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """

    def wrap(cls: EnumMeta) -> StrawberryEnum:
        return _process_enum(cls, name, description)

    if not _cls:
        return wrap

    return wrap(_cls)
