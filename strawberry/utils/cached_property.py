from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from threading import RLock
    from typing import Any, Callable, Generic, Optional, Type, TypeVar, overload

    _T = TypeVar("_T")
    _S = TypeVar("_S")

    class cached_property(Generic[_T]):  # type: ignore[no-redef]
        func: Callable[[Any], _T]
        attrname: Optional[str]
        lock: RLock

        def __init__(self, func: Callable[[Any], _T]) -> None:
            ...

        @overload  # type: ignore[no-overload-impl]
        def __get__(
            self, instance: None, owner: Optional[Type[Any]] = ...
        ) -> cached_property[_T]:
            ...

        @overload
        def __get__(self, instance: _S, owner: Optional[Type[Any]] = ...) -> _T:
            ...

        def __set_name__(self, owner: Type[Any], name: str) -> None:
            ...


__all__ = ["cached_property"]
