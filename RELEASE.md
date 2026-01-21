Release type: patch

This release fixes an issue where lazy union types using the new `Annotated` syntax were not being resolved correctly.

Example that now works:

```python
from typing import Annotated

import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def example(self) -> Annotated["SomeUnion", strawberry.lazy("module")]: ...
```
