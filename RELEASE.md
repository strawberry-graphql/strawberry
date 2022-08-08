Release type: minor

This release adds full support for Apollo Federation 2.0. To opt-in you need to
pass `enable_federation_2=True` to `strawberry.federation.Schema`, like in the
following example:

```python
@strawberry.federation.type(keys=["id"])
class User:
    id: strawberry.ID

@strawberry.type
class Query:
    user: User

schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)
```

This release also improves type checker support for the federation.
