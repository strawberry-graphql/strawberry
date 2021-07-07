Release type: minor

This release adds support for disabling auto camel casing. It
does so by introducing a new configuration parameter to the schema.

You can use it like so:

```python
@strawberry.type
class Query:
    example_field: str = "Example"

schema = strawberry.Schema(
    query=Query, config=StrawberryConfig(auto_camel_case=False)
)
```
