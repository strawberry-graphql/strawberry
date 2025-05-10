import typing
from typing import TYPE_CHECKING, Any, Generic, TypeVar, Union
from typing_extensions import TypeAlias

T = TypeVar("T")


class Some(Generic[T]):
    """A special value that can be used to represent an unset value in a field or argument.

    Similar to `undefined` in JavaScript, this value can be used to differentiate between
    a field that was not set and a field that was set to `None` or `null`.
    """

    __slots__ = ("value",)

    def __init__(self, value: T) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"Some({self.value!r})"

    def __eq__(self, other: object) -> bool:
        return self.value == other.value if isinstance(other, Some) else False

    def __hash__(self) -> int:
        return hash(self.value)

    def __bool__(self) -> bool:
        return True


if TYPE_CHECKING:
    Maybe: TypeAlias = Union[Some[Union[T, None]], None]
else:
    # we do this trick so we can inspect that at runtime
    class Maybe(Generic[T]): ...


def _annotation_is_maybe(annotation: Any) -> bool:
    return (orig := typing.get_origin(annotation)) and orig is Maybe


__all__ = [
    "Maybe",
    "Some",
]
