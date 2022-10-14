Release type: patch

This release fixes an issue that prevented using lazy types inside
generic types.

The following is now allowed:

```python
T = TypeVar("T")

TypeAType = Annotated["TypeA", strawberry.lazy("tests.schema.test_lazy.type_a")]

@strawberry.type
class Edge(Generic[T]):
    node: T

@strawberry.type
class Query:
    users: Edge[TypeAType]
```
