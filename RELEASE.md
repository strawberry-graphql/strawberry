Release type: minor

Add ability to specify description for enum values, E.g.,

```python
from enum import Enum
from typing import Annotated
import strawberry

@strawberry.enum
class SortMode(Enum):
    NEW: Annotated[
        str, strawberry.enum_value(description="Newest items first")
    ] = "new"

    HOT: Annotated[
        str, strawberry.enum_value(description="Popular items first")
    ] = "hot"

    RANDOM: Annotated[
        str, strawberry.enum_value(description="Shuffled order")
    ] = "random"
```
