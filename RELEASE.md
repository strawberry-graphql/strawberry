Release type: patch

This release fixes an issue when using named union types in generic types,
for example using an optional union. This is now properly supported:


```python
@strawberry.type
class A:
    a: int

@strawberry.type
class B:
    b: int

Result = strawberry.union("Result", (A, B))

@strawberry.type
class Query:
    ab: Optional[Result] = None
```
