from typing import Optional, TypeVar


T = TypeVar("T")


def pick_not_none(*args: Optional[T]) -> T:
    """
    Returns the first not-None argument.

    Otherwise raises ValueError
    """
    for arg in args:
        if arg is not None:
            return arg
    raise ValueError("Expected not-None argument")
