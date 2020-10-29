from typing import Callable, Generic, List, Optional, Type, TypeVar

from cached_property import cached_property

from strawberry.arguments import get_arguments_from_resolver
from strawberry.types.types import ArgumentDefinition
from strawberry.utils.inspect import get_func_args

T = TypeVar("T")


class StrawberryResolver(Generic[T]):
    def __init__(self, func: Callable[..., T], *,
                 description: Optional[str] = None):
        self.wrapped_func = func
        self._description = description

    def __call__(self, *args, **kwargs) -> T:
        return self.wrapped_func(*args, **kwargs)

    # TODO: Return StrawberryArguments instead
    # TODO: Return a set instead
    @cached_property
    def arguments(self) -> List[ArgumentDefinition]:
        return list(get_arguments_from_resolver(self.wrapped_func))

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
        return "self" in args

    @property
    def description(self) -> Optional[str]:
        # TODO: Do resolvers get descriptions?
        return self._description

    @property
    def name(self) -> str:
        # TODO: What to do if resolver is a lambda?
        return self.wrapped_func.__name__

    @property
    def type(self) -> Type[T]:
        return self.wrapped_func.__annotations__.get("return", None)
