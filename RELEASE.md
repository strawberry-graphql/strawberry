Release type: minor

This release adds a new configuration to disable field suggestions in the error
response.

```python
@strawberry.type
class Query:
    name: str


schema = strawberry.Schema(query=Query, config=StrawberryConfig(suggest_field=False))
```

Trying to query `{ nam }` will not suggest to query `name` instead.
