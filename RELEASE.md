Release type: patch

This release fixes an issue that prevented using enums that
were using strawberry.enum_value, like the following example:

```python
from enum import Enum
import strawberry

@strawberry.enum
class TestEnum(Enum):
    A = strawberry.enum_value("A")
    B = "B"

@strawberry.type
class Query:
    @strawberry.field
    def receive_enum(self, test: TestEnum) -> int:
        return 0

schema = strawberry.Schema(query=Query)
```
