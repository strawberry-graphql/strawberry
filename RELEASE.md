Release type: patch

This releases fixes a MyPy issue that prevented from using types created with
`create_type` as base classes. This is now allowed and doesn't throw any error:

```python
import strawberry
from strawberry.tools import create_type

@strawberry.field
def name() -> str:
    return "foo"

MyType = create_type("MyType", [name])

class Query(MyType):
    ...
```
