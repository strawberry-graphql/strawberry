Release type: patch

This release allows to create a federation schema without having to pass a
`Query` type. This is useful when your schema only extends some types without
adding any additional root field.

```python
@strawberry.federation.type(keys=["id"])
class Location:
    id: strawberry.ID
    name: str = strawberry.federation.field(override="start")

schema = strawberry.federation.Schema(types=[Location])
```
