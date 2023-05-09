Release type: patch

This release adds support for using `enum_value` with `IntEnum`s, like this:

```python
import strawberry

from enum import IntEnum


@strawberry.enum
class Color(IntEnum):
    OTHER = strawberry.enum_value(
        -1, description="Other: The color is not red, blue, or green."
    )
    RED = strawberry.enum_value(0, description="Red: The color red.")
    BLUE = strawberry.enum_value(1, description="Blue: The color blue.")
    GREEN = strawberry.enum_value(2, description="Green: The color green.")
```
