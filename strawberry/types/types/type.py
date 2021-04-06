from typing import Generic, List, Optional, Type, TypeVar, Union

T = TypeVar("T")


class StrawberryType(Generic[T]):

    def __init__(self, type_: Type[T]):
        self.type_ = type_

    @property
    def is_generic(self) -> bool:
        # TODO: Implement
        ...

    @property
    def is_list(self) -> bool:
        return self._origin is List

    @property
    def is_optional(self) -> bool:
        if not self.is_union:
            return False

    @property
    def is_type_var(self) -> bool:
        # TODO: Implement
        ...

    @property
    def is_union(self) -> bool:
        # TODO: Support for strawberry.Union?
        return self._origin is Union

    @property
    def _origin(self) -> Optional[...]:  # TODO: return type
        return getattr(self, "__origin__", None)
