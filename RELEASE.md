release type: patch

Fixes type hint for StrawberryTypeFromPydantic._pydantic_type to be a Type instead of an instance of the Pydantic model.
As it is a private API, we still highly discourage using it, but it's now typed correctly.

```python
from pydantic import BaseModel
from typing import Type, List

import strawberry
from strawberry.experimental.pydantic.conversion_types import StrawberryTypeFromPydantic


class User(BaseModel):
    name: str

    @staticmethod
    def foo() -> List[str]:
        return ["Patrick", "Pietro", "Pablo"]


@strawberry.experimental.pydantic.type(model=User, all_fields=True)
class UserType:
    @strawberry.field
    def foo(self: StrawberryTypeFromPydantic[User]) -> List[str]:
        # This is now inferred correctly as Type[User] instead of User
        # We still highly discourage using this private API, but it's
        # now typed correctly
        pydantic_type: Type[User] = self._pydantic_type
        return pydantic_type.foo()


def get_users() -> UserType:
    user: User = User(name="Patrick")
    return UserType.from_pydantic(user)


@strawberry.type
class Query:
    user: UserType = strawberry.field(resolver=get_users)


schema = strawberry.Schema(query=Query)
```
