Release type: patch

This releases fixed an issue that prevented from using `ID` and `GlobalID` at the same
time, like in this example:

```python
import strawberry
from strawberry.relay.types import GlobalID


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, id: GlobalID) -> str:
        return "Hello World"

    @strawberry.field
    def hello2(self, id: strawberry.ID) -> str:
        return "Hello World"


schema = strawberry.Schema(
    Query,
)
```
