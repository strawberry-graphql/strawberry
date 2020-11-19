Release type: patch

This release fixes an issue when usign unions inside generic types, this is now
supported:


```python
@strawberry.type
class Dog:
    name: str

@strawberry.type
class Cat:
    name: str

@strawberry.type
class Connection(Generic[T]):
    nodes: List[T]

@strawberry.type
class Query:
    connection: Connection[Union[Dog, Cat]]
```
