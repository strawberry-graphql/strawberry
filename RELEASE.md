Release type: patch

Fix generation of input based on pydantic models using nested `Annotated` type annotations:

```python
import strawberry
from pydantic import BaseModel


class User(BaseModel):
    age: Optional[Annotated[int, "metadata"]]


@strawberry.experimental.pydantic.input(all_fields=True)
class UserInput:
    pass
```
