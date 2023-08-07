import asyncio
import inspect
from functools import lru_cache
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
)
from typing_extensions import get_args

from strawberry.type import has_object_definition


def in_async_context() -> bool:
    # Based on the way django checks if there's an event loop in the current thread
    # https://github.com/django/django/blob/main/django/utils/asyncio.py
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    else:
        return True


@lru_cache(maxsize=250)
def get_func_args(func: Callable[[Any], Any]) -> List[str]:
    """Returns a list of arguments for the function"""

    sig = inspect.signature(func)

    return [
        arg_name
        for arg_name, param in sig.parameters.items()
        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]


def get_specialized_type_var_map(cls: type) -> Optional[Dict[str, type]]:
    """Get a type var map for specialized types.

    Consider the following:

        >>> class Foo(Generic[T]):
        ...     ...
        ...
        >>> class Bar(Generic[K]):
        ...     ...
        ...
        >>> class IntBar(Bar[int]):
        ...     ...
        ...
        >>> class IntBarSubclass(IntBar):
        ...     ...
        ...
        >>> class IntBarFoo(IntBar, Foo[str]):
        ...     ...
        ...

    This would return:

        >>> get_specialized_type_var_map(object)
        None
        >>> get_specialized_type_var_map(Foo)
        {}
        >>> get_specialized_type_var_map(Bar)
        {~T: ~T}
        >>> get_specialized_type_var_map(IntBar)
        {~T: int}
        >>> get_specialized_type_var_map(IntBarSubclass)
        {~T: int}
        >>> get_specialized_type_var_map(IntBarFoo)
        {~T: int, ~K: str}

    """
    orig_bases = getattr(cls, "__orig_bases__", None)
    if orig_bases is None:
        # Not a specialized type
        return None

    type_var_map = {}

    # only get type vars for base generics (ie. Generic[T]) and for strawberry types

    orig_bases = [b for b in orig_bases if has_object_definition(b)]

    for base in orig_bases:
        # Recursively get type var map from base classes
        base_type_var_map = get_specialized_type_var_map(base)
        if base_type_var_map is not None:
            type_var_map.update(base_type_var_map)

        args = get_args(base)
        origin = getattr(base, "__origin__", None)

        params = origin and getattr(origin, "__parameters__", None)
        if params is None:
            params = getattr(base, "__parameters__", None)

        if not params:
            continue

        type_var_map.update(
            {p.__name__: a for p, a in zip(params, args) if not isinstance(a, TypeVar)}
        )

    return type_var_map
