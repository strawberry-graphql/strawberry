import asyncio
import inspect
from functools import lru_cache
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

import strawberry


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
def get_func_args(func: Callable[[Any], Any]) -> list[str]:
    """Returns a list of arguments for the function."""
    sig = inspect.signature(func)

    return [
        arg_name
        for arg_name, param in sig.parameters.items()
        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]


def get_specialized_type_var_map(cls: type) -> Optional[dict[str, type]]:
    """Get a type var map for specialized types.

    Consider the following:

    ```python
    class Foo(Generic[T]): ...


    class Bar(Generic[K]): ...


    class IntBar(Bar[int]): ...


    class IntBarSubclass(IntBar): ...


    class IntBarFoo(IntBar, Foo[str]): ...
    ```

    This would return:

    ```python
    get_specialized_type_var_map(object)
    # None

    get_specialized_type_var_map(Foo)
    # {}

    get_specialized_type_var_map(Bar)
    # {}

    get_specialized_type_var_map(IntBar)
    # {~T: int, ~K: int}

    get_specialized_type_var_map(IntBarSubclass)
    # {~T: int, ~K: int}

    get_specialized_type_var_map(IntBarFoo)
    # {~T: int, ~K: str}
    ```
    """
    from strawberry.types.base import has_object_definition

    param_args: dict[TypeVar, Union[TypeVar, type]] = {}

    types: list[type] = [cls]
    while types:
        tp = types.pop(0)
        if (origin := get_origin(tp)) is None or origin in (Generic, Protocol):
            origin = tp

        # only get type vars for base generics (i.e. Generic[T]) and for strawberry types
        if not has_object_definition(origin):
            continue

        if (type_params := getattr(origin, "__parameters__", None)) is not None:
            args = get_args(tp)
            if args:
                for type_param, arg in zip(type_params, args):
                    if type_param not in param_args:
                        param_args[type_param] = arg
            else:
                for type_param in type_params:
                    if type_param not in param_args:
                        param_args[type_param] = strawberry.UNSET

        if orig_bases := getattr(origin, "__orig_bases__", None):
            types.extend(orig_bases)
    if not param_args:
        return None

    for type_param, arg in list(param_args.items()):
        resolved_arg = arg
        while (
            isinstance(resolved_arg, TypeVar) and resolved_arg is not strawberry.UNSET
        ):
            resolved_arg = (
                param_args.get(resolved_arg, strawberry.UNSET)
                if resolved_arg is not type_param
                else strawberry.UNSET
            )

        param_args[type_param] = resolved_arg

    return {
        k.__name__: v
        for k, v in reversed(param_args.items())
        if v is not strawberry.UNSET and not isinstance(v, TypeVar)
    }


__all__ = ["get_func_args", "get_specialized_type_var_map", "in_async_context"]
