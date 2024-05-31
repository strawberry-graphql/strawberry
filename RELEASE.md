Release type: patch

This release fixes a typing issue where trying to type a `root` argument with
`strawberry.Parent` would fail, like in the following example:

```python
import strawberry

@strawberry.type
class SomeType:
    @strawberry.field
    def hello(self, root: strawberry.Parent[str]) -> str:
        return "world"
```

This should now work as intended.
