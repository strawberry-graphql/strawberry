Release type: patch

This release fixes the naming generation of generics when
passing a generic type to another generic, like so:

```python
@strawberry.type
class Edge(Generic[T]):
    node: T

@strawberry.type
class Connection(Generic[T]):
    edges: List[T]

Connection[Edge[int]]
```
