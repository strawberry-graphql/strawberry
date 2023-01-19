import inspect
from functools import lru_cache
from typing import Any, Callable


@lru_cache(maxsize=250)
def get_func_args(func: Callable[[Any], Any]):
    """Returns a list of arguments for the function"""

    sig = inspect.signature(func)

    return [
        arg_name
        for arg_name, param in sig.parameters.items()
        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]
