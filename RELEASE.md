Release type: patch

This release fixes an issue that would prevent using generics with unnamed
unions, like in this example:

```python
from typing import Generic, TypeVar, Union
import strawberry

T = TypeVar("T")


@strawberry.type
class Connection(Generic[T]):
    nodes: list[T]


@strawberry.type
class Entity1:
    id: int


@strawberry.type
class Entity2:
    id: int


@strawberry.type
class Query:
    entities: Connection[Union[Entity1, Entity2]]
```
