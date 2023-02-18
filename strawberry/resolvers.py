from typing import Any, Callable


def is_default_resolver(func: Callable[..., Any]) -> bool:
    """Check whether the function is a default resolver or a user provided one."""
    return getattr(func, "_is_default", False)
