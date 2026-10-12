import asyncio
import inspect
from collections.abc import Callable, Mapping
from functools import lru_cache
from typing import (
    Any,
    Generic,
    Protocol,
    TypeVar,
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


def get_specialized_type_var_map(cls: type) -> dict[str, type] | None:
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

    param_args: dict[TypeVar, TypeVar | type] = {}

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
                for type_param, arg in zip(type_params, args, strict=True):
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


def _split_generic_alias(base: Any) -> tuple[Any, tuple[Any, ...]]:
    """Return the class of a base and its arguments, like `(Page, (int,))`."""
    return get_origin(base) or base, get_args(base)


def _replace_type_vars(type_: Any, type_vars: Mapping[Any, Any]) -> Any:
    """Replace the type parameters in `type_`, like `U` in `list[U]`."""
    if isinstance(type_, TypeVar):
        return type_vars.get(type_, type_)

    # only aliases like `list[U]` have parameters to replace: a generic class
    # like `Page` stands for `Page[Any]`
    parameters = (
        getattr(type_, "__parameters__", ()) if get_origin(type_) is not None else ()
    )

    if not any(parameter in type_vars for parameter in parameters):
        return type_

    return type_[tuple(type_vars.get(parameter, parameter) for parameter in parameters)]


def get_generic_arguments(
    cls: Any,
    split_base: Callable[[Any], tuple[Any, tuple[Any, ...]]] = _split_generic_alias,
) -> dict[type, dict[Any, Any]]:
    """Return the arguments `cls` gives to the type parameters of its generic bases.

    They're grouped by the generic class declaring the type parameters, so the
    type parameters of different bases don't get mixed up, even when they have
    the same name or are the same `TypeVar`:

    ```python
    class Page(Generic[T]): ...


    class Label(Generic[T]): ...


    class Wrapper(Page[list[U]], Generic[U]): ...


    class IntWrapper(Wrapper[int], Label[str]): ...


    get_generic_arguments(IntWrapper)
    # {IntWrapper: {}, Wrapper: {~U: int}, Page: {~T: list[int]}, Label: {~T: str}}
    ```

    Arguments that use the type parameters of the class extending the base, like
    `list[U]`, get that class's arguments. `split_base` returns the class and the
    arguments of a base, like `(Page, (int,))` for `Page[int]`, and can be
    replaced for classes that aren't parametrized with `typing` aliases, like
    Pydantic's generic models.
    """
    arguments: dict[type, dict[Any, Any]] = {}

    def add(base: Any, type_vars: Mapping[Any, Any]) -> None:
        origin, args = split_base(base)

        # e.g. `Generic[T]`, which declares the parameters of the class extending it
        if not isinstance(origin, type) or origin in (Generic, Protocol):
            return

        # like the MRO, the first base wins
        if origin in arguments:
            return

        parameters = getattr(origin, "__parameters__", ())
        arguments[origin] = origin_arguments = {
            parameter: _replace_type_vars(argument, type_vars)
            for parameter, argument in zip(parameters, args, strict=False)
        }

        # the class's own bases, as `__orig_bases__` is inherited by subclasses
        # that don't define it
        for origin_base in vars(origin).get("__orig_bases__", origin.__bases__):
            add(origin_base, origin_arguments)

    add(cls, {})

    return arguments


__all__ = [
    "get_func_args",
    "get_generic_arguments",
    "get_specialized_type_var_map",
    "in_async_context",
]
