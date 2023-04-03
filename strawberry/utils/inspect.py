import inspect
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, overload
from typing_extensions import Literal, get_args


@lru_cache(maxsize=250)
def get_func_args(func: Callable[[Any], Any]) -> List[str]:
    """Returns a list of arguments for the function"""

    sig = inspect.signature(func)

    return [
        arg_name
        for arg_name, param in sig.parameters.items()
        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]


@overload
def get_specialized_type_var_map(
    cls: type,
    *,
    include_type_vars: Literal[True],
) -> Optional[Dict[TypeVar, Union[TypeVar, type]]]:
    ...


@overload
def get_specialized_type_var_map(
    cls: type,
    *,
    include_type_vars: Literal[False] = ...,
) -> Optional[Dict[TypeVar, type]]:
    ...


@overload
def get_specialized_type_var_map(
    cls: type,
    *,
    include_type_vars: bool,
) -> Optional[
    Union[Optional[Dict[TypeVar, type]], Dict[TypeVar, Union[TypeVar, type]]]
]:
    ...


def get_specialized_type_var_map(cls: type, *, include_type_vars: bool = False):
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
        >>> get_specialized_type_var_map(Foo, include_type_vars=True)
        {~T: ~T}
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
            {
                p: a
                for p, a in zip(params, args)
                if include_type_vars or not isinstance(a, TypeVar)
            }
        )

    return type_var_map
