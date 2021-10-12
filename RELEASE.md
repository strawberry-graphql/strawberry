Release type: patch

Pydantic fields' `description` are now copied to the GraphQL schema

```python
import pydantic
import strawberry


class UserModel(pydantic.BaseModel):
    age: int
    password: str = pydantic.Field(..., description="HUGE DESCRIPTION.")


@strawberry.experimental.pydantic.type(UserModel)
class User:
    age: strawberry.auto
    password: strawberry.auto
```

```
type User {
  age: Int!

  """HUGE DESCRIPTION."""
  password: String!
}
```
