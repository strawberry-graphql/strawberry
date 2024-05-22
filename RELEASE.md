Release type: patch

This release fixes an issue when using `Annotated` + `strawberry.lazy` +
deferred annotations such as:

```python
from __future__ import annotations
import strawberry
from typing import Annotated


@strawberry.type
class Query:
    a: Annotated["datetime", strawberry.lazy("datetime")]


schema = strawberry.Schema(Query)
```

Before this would only work if `datetime` was not inside quotes. Now it should
work as expected!
