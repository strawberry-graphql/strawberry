import warnings
from typing import Any, Dict, Optional, Type

DEPRECATED_NAMES: Dict[str, str] = {
    "is_unset": "`is_unset` is deprecated use `value is UNSET` instead",
}


class UnsetType:
    __instance: Optional["UnsetType"] = None

    def __new__(cls: Type["UnsetType"]) -> "UnsetType":
        if cls.__instance is None:
            ret = super().__new__(cls)
            cls.__instance = ret
            return ret
        else:
            return cls.__instance

    def __str__(self) -> str:
        return ""

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False


UNSET: Any = UnsetType()
"""A special value that can be used to represent an unset value in a field or argument.
Similar to `undefined` in JavaScript, this value can be used to differentiate between
a field that was not set and a field that was set to `None` or `null`.

Example:

```python
import strawberry


@strawberry.input
class UserInput:
    name: str | None = strawberry.UNSET
    age: int | None = strawberry.UNSET
```

In the example above, if `name` or `age` are not provided when creating a `UserInput`
object, they will be set to `UNSET` instead of `None`. Use `is UNSET` to check
whether a value is unset.
"""


def _deprecated_is_unset(value: Any) -> bool:
    warnings.warn(DEPRECATED_NAMES["is_unset"], DeprecationWarning, stacklevel=2)
    return value is UNSET


def __getattr__(name: str) -> Any:
    if name in DEPRECATED_NAMES:
        warnings.warn(DEPRECATED_NAMES[name], DeprecationWarning, stacklevel=2)
        return globals()[f"_deprecated_{name}"]
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "UNSET",
]
