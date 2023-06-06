Release type: minor

This release adds support for properly resolving lazy references
when using forward refs.

For example, this code should now work without any issues:

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

if TYPE_CHECKING:
    from some.module import OtherType


@strawberry.type
class MyType:
    @strawberry.field
    async def other_type(self) -> Annotated[OtherType, strawberry.lazy("some.module")]:
        ...
```
