Release type: patch

Copied pydantic field's `description`.

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