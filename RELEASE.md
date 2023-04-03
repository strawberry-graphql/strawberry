release type: patch

Fixes type hint for StrawberryTypeFromPydantic._pydantic_type to be a Type instead of a class.

```python
from pydantic import BaseModel
from typing import Type

import strawberry


class User(BaseModel):
    name: str
    
    @staticmethod
    def available_names() -> list[str]:
        return ["Patrick", "Pietro", "Pablo"]

@strawberry.experimental.pydantic.type(model=User, all_fields=True)
class UserType:
    ...

def get_users() -> UserType:
    # Previously the type hint for UserType._pydantic_type
    # was an instance of User instead of a Type
    pydantic_type: Type[User] = UserType._pydantic_type
    user: User =  pydantic_type(name="Patrick")
    return UserType.from_pydantic(user)


@strawberry.type
class Query:
    user: UserType = strawberry.field(resolver=get_users)


schema = strawberry.Schema(query=Query)
```
