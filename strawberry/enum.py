import dataclasses
from enum import EnumMeta
from typing import Any, Callable, List, Optional, Union

from .exceptions import NotAnEnum


@dataclasses.dataclass
class EnumValue:
    name: str
    value: Any


@dataclasses.dataclass(frozen=True)
class StrawberryEnum:
    enum: EnumMeta
    # TODO: graphql_name, python_name
    name: str
    values: List[EnumValue] = dataclasses.field(hash=False)
    description: Optional[str]

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.enum(*args, **kwds)

    def __getattr__(self, attr):
        if hasattr(self.enum, attr):
            return self.enum[attr]

        return super().__getattribute__(attr)


def _process_enum(
    cls: EnumMeta, name: Optional[str] = None, description: Optional[str] = None
) -> StrawberryEnum:
    if not isinstance(cls, EnumMeta):
        raise NotAnEnum()

    if not name:
        name = cls.__name__

    description = description

    values = [EnumValue(item.name, item.value) for item in cls]  # type: ignore

    return StrawberryEnum(
        enum=cls,
        name=name,
        values=values,
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
