Release type: patch

Allow use of implicit `Any` in `strawberry.Private` annotated Generic types.

For example the following is now supported:

```python
from __future__ import annotations

from typing import Generic, Sequence, TypeVar

import strawberry


T = TypeVar("T")


@strawberry.type
class Foo(Generic[T]):

    private_field: strawberry.Private[Sequence]  # instead of Sequence[Any]


@strawberry.type
class Query:
    @strawberry.field
    def foo(self) -> Foo[str]:
        return Foo(private_field=[1, 2, 3])
```

See Issue [#1938](https://github.com/strawberry-graphql/strawberry/issues/1938)
for details.
