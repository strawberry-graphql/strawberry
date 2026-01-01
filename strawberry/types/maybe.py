import re
import typing
from typing import TYPE_CHECKING, Annotated, Any, Generic, TypeAlias, TypeVar

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
    Maybe: TypeAlias = Some[T] | None
else:
    # we do this trick so we can inspect that at runtime
    class Maybe(Generic[T]): ...


_maybe_re = re.compile(r"^(?:strawberry\.)?Maybe\[(.+)\]$")


def _annotation_is_maybe(annotation: Any) -> bool:
    if isinstance(annotation, str):
        # Ideally we would try to evaluate the annotation, but the args inside
        # may still not be available, as the module is still being constructed.
        # Checking for the pattern should be good enough for now.
        return _maybe_re.match(annotation) is not None

    orig = typing.get_origin(annotation)
    if orig is Annotated:
        return _annotation_is_maybe(typing.get_args(annotation)[0])
    return orig is Maybe


__all__ = [
    "Maybe",
    "Some",
]
