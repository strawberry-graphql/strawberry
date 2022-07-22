Release type: minor

This release adds support for overriding the default resolver for fields.

Currentily the default resolver is `getattr`, but now you can change it to any
function you like, for example you can allow returning dictionaries:


```python
@strawberry.type
class User:
    name: str

@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return {"name": "Patrick"}  # type: ignore

schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(default_resolver=getitem),
)

query = "{ user { name } }"

result = schema.execute_sync(query)
```
