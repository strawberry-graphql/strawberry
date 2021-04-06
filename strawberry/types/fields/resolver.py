from inspect import iscoroutinefunction
from typing import Callable, Optional, Set, TypeVar, Generic

from cached_property import cached_property  # type: ignore

from strawberry.types import StrawberryArgument, StrawberryType
from strawberry.utils.inspect import get_func_args

T = TypeVar("T")


class StrawberryResolver(Generic[T]):
    def __init__(self, func: Callable[..., T], *, description: Optional[str] = None):
        self.wrapped_func = func
        self._description = description

    # TODO: Use this when doing the actual resolving? How to deal with async resolvers?
    def __call__(self, *args, **kwargs) -> T:
        return self.wrapped_func(*args, **kwargs)

    @cached_property
    def arguments(self) -> Set[StrawberryArgument]:
        # TODO: Implement
        ...

    @cached_property
    def has_info_arg(self) -> bool:
        args = get_func_args(self.wrapped_func)
        return "info" in args

    @cached_property
    def has_root_arg(self) -> bool:
        args = get_func_args(self.wrapped_func)
        return "root" in args

    @cached_property
    def has_self_arg(self) -> bool:
        args = get_func_args(self.wrapped_func)
        return args and args[0] == "self"

    @cached_property
    def name(self) -> str:
        # TODO: What to do if resolver is a lambda?
        return self.wrapped_func.__name__

    @cached_property
    def type(self) -> Optional[StrawberryType[T]]:
        type_ = self.wrapped_func.__annotations__.get("return", None)

        if type_ is not None:
            type_ = StrawberryType(type_)

        return type_

    @cached_property
    def is_async(self) -> bool:
        return iscoroutinefunction(self.wrapped_func)


__all__ = ["StrawberryResolver"]
