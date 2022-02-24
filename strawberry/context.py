import contextvars
from typing import Any, Generic, TypeVar

from strawberry.types.info import Info


RootType = TypeVar("RootType", bound=Any)
InfoType = TypeVar("InfoType", bound=Info[Any, Any])


_root = contextvars.ContextVar("_root")
_info = contextvars.ContextVar("_info")


class Context(Generic[InfoType, RootType]):
    @property
    def root(self) -> RootType:
        return _root.get()

    @root.setter
    def root(self, value: RootType):
        _root.set(value)

    @property
    def info(self) -> InfoType:
        return _info.get()

    @info.setter
    def info(self, value: InfoType):
        _info.set(value)


context = Context()
