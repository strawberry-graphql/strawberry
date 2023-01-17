Release type: patch

Fix `DuplicatedTypeName` exception being raised on generics declared using
`strawberry.lazy`. Previously the following would raise:

```python
# issue_2397.py
from typing import Annotated, Generic, TypeVar

import strawberry

T = TypeVar("T")


@strawberry.type
class Item:
    name: str


@strawberry.type
class Edge(Generic[T]):
    node: T


@strawberry.type
class Query:
    edges_normal: Edge[Item]
    edges_lazy: Edge[Annotated["Item", strawberry.lazy("issue_2397")]]


if __name__ == "__main__":
    schema = strawberry.Schema(query=Query)
```
