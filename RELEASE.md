Release type: minor

This release features a dedicated extension to disable introspection queries.
Disabling introspection queries was already possible using the
`AddValidationRules` extension. However, using this new extension requires less
steps and makes the feature more discoverable.

## Usage example:

```python
import strawberry
from strawberry.extensions import DisableIntrospection


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, world!"


schema = strawberry.Schema(
    Query,
    extensions=[
        DisableIntrospection(),
    ],
)
```
