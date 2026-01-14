Release type: patch

This release fixes an issue where `relay.node()` fields on nested types required
explicit initialization, even though the field values are resolved dynamically.

Previously, this code would fail at runtime:

```python
@strawberry.type
class Sub:
    node: relay.Node = relay.node()


@strawberry.type
class Query:
    @strawberry.field
    def sub(self) -> Sub:
        return Sub()  # Error: missing required argument 'node'
```

Now `relay.node()` provides a default value, allowing nested types with relay
node fields to be instantiated without explicit initialization.
