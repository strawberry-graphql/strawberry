Release type: minor

This release adds support for `typing.Self` and `typing_extensions.Self` for types and interfaces.

```python
from typing_extensions import Self

@strawberry.type
class Node:
    @strawberry.field
    def field(self) -> Self:
        return self
```
