from enum import EnumMeta
from typing import Any, Callable, Mapping, Optional, TypeVar, Union, overload

from strawberry.type import StrawberryType
from strawberry.utils.mixins import GraphQLNameMixin

from .exceptions import NotAnEnum


class StrawberryEnum(GraphQLNameMixin, StrawberryType):
    def __init__(
        self,
        enum: EnumMeta,
        python_name: str,
        graphql_name: Optional[str],
        description: Optional[str],
    ) -> None:
        self.enum = enum
        self.python_name = python_name
        self.graphql_name = graphql_name
        self.description = description

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.enum(*args, **kwds)

    def __getattr__(self, attr: str) -> object:
        if hasattr(self.enum, attr):
            return getattr(self.enum, attr)

        return super().__getattribute__(attr)

    def __getitem__(self, item: str) -> object:
        return self.enum[item]

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> Union[StrawberryType, type]:
        return super().copy_with(type_var_map)

    @property
    def is_generic(self) -> bool:
        return False


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


# not using bound=EnumMeta because it's PyRight doesn't support it properly
T = TypeVar("T")


@overload
def enum(cls: T, *, name: Optional[str] = None, description: Optional[str] = None) -> T:
    ...


@overload
def enum(
    *, name: Optional[str] = None, description: Optional[str] = None
) -> Callable[[T], T]:
    ...


def enum(cls=None, *, name=None, description=None):
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """

    def wrap(cls: T) -> T:
        return _process_enum(cls, name, description)  # type: ignore

    if not cls:
        return wrap

    return wrap(cls)
