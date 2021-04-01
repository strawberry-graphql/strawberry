Release type: patch

This relases fixes an issue with the generated `__eq__` and `__repr__` methods when defining
fields with resolvers.

This now works properly:

```python
@strawberry.type
class Query:
    a: int

    @strawberry.field
    def name(self) -> str:
        return "A"

assert Query(1) == Query(1)
assert Query(1) != Query(2)
```
