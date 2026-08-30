Release type: minor

Add a new `lexicographic_sort_schema` option to `StrawberryConfig`. When enabled,
the schema's types, fields and arguments are sorted alphabetically, affecting both
the introspection result and the exported SDL. This makes it easier to find
related fields (for example `userById`, `userByName`) in the GraphiQL UI and in
exported `schema.graphql` files.

```python
import strawberry
from strawberry.schema.config import StrawberryConfig

schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(lexicographic_sort_schema=True),
)
```

It defaults to `False`, preserving the existing definition order.
