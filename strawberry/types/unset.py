from typing import Any
from typing_extensions import Self


class UnsetType:
    __instance: Self | None = None

    def __new__(cls: type[Self]) -> Self:
        if cls.__instance is None:
            ret = super().__new__(cls)
            cls.__instance = ret
            return ret
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

__all__ = [
    "UNSET",
]
