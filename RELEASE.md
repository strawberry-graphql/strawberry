Release type: minor

This PR adds a MaxAliasesLimiter extensions which limits the number of aliases in a GraphQL document.

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
