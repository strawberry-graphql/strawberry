Release type: patch

Fixes an issue where a pydantic type that is required, with a default, would get converted to a strawberry type that is not required.
This makes the behavior consistent with the behavior of normal strawberry types.

```python
class UserPydantic(pydantic.BaseModel):
    name: str = "James"

@strawberry.experimental.pydantic.type(UserPydantic, all_fields=True)
class User:
    ...

@strawberry.type
class Query:
    a: User = strawberry.field()

    @strawberry.field
    def a(self) -> User:
        return User()
```
The schema is now
```
type Query {
  a: User!
}

type User {
  name: String! // String! rather than String previously
}
```
