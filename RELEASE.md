Release type: minor

This release adds a new configuration to disable field suggestions in the error
response.

```python
@strawberry.type
class Query:
    name: str


schema = strawberry.Schema(
    query=Query, config=StrawberryConfig(disable_field_suggestions=True)
)
```

Trying to query `{ nam }` will not suggest to query `name` instead.
