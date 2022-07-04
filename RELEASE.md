Release type: patch

Fix regression caused by the new resolver argument handling mechanism
introduced in v0.115.0. This release restores the ability to use unhashable
default values in resolvers such as dict and list. See example below:

```python
@strawberry.type
class Query:
    @strawberry.field
    def field(
        self, x: List[str] = ["foo"], y: JSON = {"foo": 42}  # noqa: B006
    ) -> str:
        return f"{x} {y}"
```

Thanks to @coady for the regression report!
