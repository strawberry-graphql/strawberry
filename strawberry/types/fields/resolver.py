from typing import Callable, Optional, Set, TypeVar

from cached_property import cached_property

from strawberry.types import StrawberryArgument, StrawberryObject, \
    StrawberryType

T = TypeVar("T")


class StrawberryResolver(StrawberryType[T]):
    def __init__(self, func: Callable[..., T], *, description: Optional[str]):
        self.wrapped_func = func
        self._description = description

    def __call__(self, *args, **kwargs) -> T:
        # TODO: Should *args/**kwargs be some special object, or raw values?

        if self._is_func_bound:
            ...
        if self._has_root_arg:
            ...
        if self._has_info_arg:
            ...

        # Deal with default args

        return self.wrapped_func(*args, **kwargs)

    @cached_property
    def arguments(self) -> Set[StrawberryArgument]:
        # TODO: Implement
        ...

    @property
    def description(self) -> Optional[str]:
        # TODO: Do resolvers get descriptions?
        return self._description

    @property
    def name(self) -> str:
        # TODO: What to do if resolver is a lambda?
        return self.wrapped_func.__name__

    # TODO: Should return type just be T?
    @property
    def type(self) -> Optional[StrawberryObject[T]]:
        annotations = self.wrapped_func.__annotations__

        if "return" not in annotations:
            return None

        return_type = annotations["return"]

        if isinstance(return_type, StrawberryObject):
            return return_type

        # TODO: Figure out what to do without name
        return StrawberryType(return_type)

    @cached_property
    def _is_func_bound(self) -> bool:
        ...

    @cached_property
    def _has_info_arg(self) -> bool:
        ...

    @property
    def _has_root_arg(self) -> bool:
        ...
