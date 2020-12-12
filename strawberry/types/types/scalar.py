from abc import abstractmethod
from typing import Any, Callable, Optional, Type, TypeVar

from strawberry.types import StrawberryType

T = TypeVar("T")


class StrawberryScalar(StrawberryType[T]):
    # TODO: I want these to be abstract, but graphql-core wants
    #       Optional[Callable] (i.e. either functions or None). Is it possible,
    #       in a nice way?
    serialize: Optional[Callable[[T], Any]]
    parse_value: Optional[Callable[[Any], T]]
    parse_literal: Optional[Callable]

    # TODO: Support serialize/deserialize as __init__ args
    def __init__(self, cls: Optional[Type[T]], *, name: Optional[str] = None,
                 description: Optional[str] = None):
        self.wrapped_class = cls
        self._name = name
        self._description = description

    def __call__(self, cls: Type[T]):
        self.wrapped_class = cls

    @abstractmethod
    def serialize(self, _: T) -> Any:
        ...

    @abstractmethod
    def parse_value(self, _: Any) -> T:
        ...

    @abstractmethod
    def parse_literal(self, _: Any) -> T:
        ...

    def name(self) -> Optional[str]:
        if self._name is not None:
            return self._name

        if self.wrapped_class:
            return self.wrapped_class.__name__

        # TODO: Should we raise an exception instead?
        return None


def scalar(cls: Optional[Type[T]] = None, *, name: Optional[str] = None,
           description: Optional[str] = None) -> StrawberryScalar:
    return StrawberryScalar(
        cls=cls,
        name=name,
        description=description
    )
