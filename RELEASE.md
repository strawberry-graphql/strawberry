Release type: minor

Improves the following for types converted from pydantic BaseModel.
Adds mypy extension support for `to_pydantic` and `from_pydantic` methods.
Adds type hints for IDE support.

```python
from pydantic import BaseModel
import strawberry

class UserPydantic(BaseModel):
    age: int

@strawberry.experimental.pydantic.type(UserPydantic)
class UserStrawberry:
    age: strawberry.auto

reveal_type(UserStrawberry(age=123).to_pydantic())
```
Mypy will infer the type as "UserPydantic". Previously it would be `Any`.
