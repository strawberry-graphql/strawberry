Release type: patch

Fix invalid deprecation warning issued on arguments annotated
by a subclassed `strawberry.types.Info`.

Thanks to @ThirVondukr for the bug report!

Example:

```python
class MyInfo(Info)
    pass

@strawberry.type
class Query:

    @strawberry.field
    def is_tasty(self, info: MyInfo) -> bool:
        """Subclassed ``info`` argument no longer raises deprecation warning."""
```
