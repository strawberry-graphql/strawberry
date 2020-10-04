from typing import Callable, Optional, Set, TypeVar

from cached_property import cached_property

from strawberry.types import StrawberryArgument, StrawberryObject, \
    StrawberryType

T = TypeVar("T")


class StrawberryResolver(StrawberryType[T]):
    def __init__(self, func: Callable[..., T], *, description: Optional[str]):
        self.wrapped_func = func
        self._description = description

    @cached_property
    def arguments(self) -> Set[StrawberryArgument]:
        # TODO: Implement
        ...

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def name(self) -> str:
        return self.wrapped_func.__name__

    @property
    def type(self) -> Optional[StrawberryObject[T]]:  # TODO: Broaden type
        annotations = self.wrapped_func.__annotations__

        if "return" not in annotations:
            return None

        return_type = annotations["return"]

        if isinstance(return_type, StrawberryObject):
            return return_type

        # TODO: Figure out what to do without name
        return StrawberryType(return_type)
