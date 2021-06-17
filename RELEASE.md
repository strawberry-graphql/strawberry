Release type: minor

Add ability to specific the graphql name for a resolver argument. E.g.,

```python
from typing import Annotated
import strawberry


@strawberry.input
class HelloInput:
    name: str = "world"


@strawberry.type
class Query:
    @strawberry.field
    def hello(
        self,
        input_: Annotated[HelloInput, strawberry.argument(name="input")]
    ) -> str:
        return f"Hi {input_.name}"
```
