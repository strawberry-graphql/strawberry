Release type: minor

Add a shortcut to merge queries, mutations. E.g.:

```python
import strawberry
from strawberry.tools import merge_types


@strawberry.type
class QueryA:
    ...


@strawberry.type
class QueryB:
    ...


ComboQuery = merge_types("ComboQuery", (QueryB, QueryA))
schema = strawberry.Schema(query=ComboQuery)
```
