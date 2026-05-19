Release type: patch

Fix `UnresolvedFieldTypeError` when using `from __future__ import annotations` together with a module-level `Annotated[..., strawberry.lazy(...)]` alias. The aliased form now resolves the same as inlining `Annotated[...]` on the field.

```python
from __future__ import annotations
from typing import TYPE_CHECKING, Annotated
import strawberry

if TYPE_CHECKING:
    from .user import User

LazyUser = Annotated["User", strawberry.lazy(".user")]


@strawberry.type
class Post:
    user: LazyUser  # previously failed
```
