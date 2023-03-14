Release type: minor

This release introduces a breaking change to make pydantic default behavior consistent with normal strawberry types.
This changes the schema generated for pydantic types, that are required, and have default values.
Previously pydantic type with a default, would get converted to a strawberry type that is not required.
This is now fixed, and the schema will now correctly show the type as required.

```python
import pydantic
import strawberry


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
