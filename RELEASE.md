Release type: patch

Fixes a bug when converting pydantic models with NewTypes in a List.
This no longers causes an exception.
 ```{python}
from typing import List, NewType
from pydantic import BaseModel
import strawberry

password = NewType("password", str)

class User(BaseModel):
    passwords: List[password]


@strawberry.experimental.pydantic.type(User)
class UserType:
    passwords: strawberry.auto

 ```
