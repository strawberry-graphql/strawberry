Release type: minor

Adds support for the `auto` type annotation described in #1192 to the Pydantic
integration, which allows a user to define the list of fields without having to
re-specify the type themselves. This gives better editor and type checker
support. If you want to expose every field you can instead pass
`all_fields=True` to the decorators and leave the body empty.

```python
import pydantic
import strawberry
from strawberry.experimental.pydantic import auto

class User(pydantic.BaseModel):
    age: int
    password: str


@strawberry.experimental.pydantic.type(User)
class UserType:
    age: auto
    password: auto
```
