from typing import Callable

from strawberry.types.fields.resolver import StrawberryResolver


def is_default_resolver(func: Callable) -> bool:
    """Check whether the function is a default resolver or a user provided one."""
    if getattr(func, "_is_default", False):
        return True

    # Check if func is a partial function
    if hasattr(func, "func"):
        resolver: StrawberryResolver = func.func  # type: ignore
        return resolver.is_default

    return False
