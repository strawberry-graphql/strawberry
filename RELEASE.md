Release type: patch

This release fixes an issue where `DuplicatedTypeName` exception would be raised
for nested generics like in the example below:

```python
from typing import Generic, TypeVar

import strawberry

T = TypeVar("T")


@strawberry.type
class Wrapper(Generic[T]):
    value: T


@strawberry.type
class Query:
    a: Wrapper[Wrapper[int]]
    b: Wrapper[Wrapper[int]]


schema = strawberry.Schema(query=Query)
```

This piece of code and similar ones will now work correctly.
