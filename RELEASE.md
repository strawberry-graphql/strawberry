Release type: patch

This release fixes support for PEP-563, now you can safely use `from __future__ import annotations`,
like the following example:


```python
from __future__ import annotations

@strawberry.type
class Query:
    me: MyType = strawberry.field(name="myself")

@strawberry.type
class MyType:
    id: strawberry.ID

```
