Release type: patch

Fix Generic name generation to use the custom name specified in Strawberry if available

```python
@strawberry.type(name="AnotherName")
class EdgeName:
    node: str

@strawberry.type
class Connection(Generic[T]):
    edge: T
```

will result in `AnotherNameConnection`, and not `EdgeNameConnection` as before.
