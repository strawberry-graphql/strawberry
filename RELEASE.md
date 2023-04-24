Release type: minor

Extension MaxAliasesLimiter
Add a validator to limit the maximum number of aliases in a GraphQL document.

## Usage example:

```python
import strawberry
from strawberry.extensions import MaxAliasesLimiter

schema = strawberry.Schema(
    Query,
    extensions=[
        MaxAliasesLimiter(max_alias_count=15),
    ],
)
```
