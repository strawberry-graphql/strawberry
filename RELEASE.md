Release type: patch

This release fixes an issue for parsing lazy types using forward references
when they were enclosed in an `Optional[...]` type.

The following now should work properly:

```python
from __future__ import annotations

from typing import Optional, Annotated
import strawberry


@strawberry.type
class MyType:
    other_type: Optional[Annotated["OtherType", strawberry.lazy("some.module")]]
    # or like this
    other_type: Annotated["OtherType", strawberry.lazy("some.module")] | None
```
