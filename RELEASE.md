Release type: patch

Pydantic fields' `description` are now copied to the GraphQL schema

```python
import pydantic
import strawberry

class UserModel(pydantic.BaseModel):
    age: str = pydantic.Field(..., description="Description")

@strawberry.experimental.pydantic.type(UserModel)
class User:
    age: strawberry.auto
```

```
type User {
  """Description"""
  age: String!
}
```
