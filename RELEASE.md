---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! The new `sort_schema` config option sorts
    your schema's types, fields and arguments alphabetically in introspection
    and exported SDL. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. It adds a `sort_schema` option to
    StrawberryConfig that sorts types, fields and arguments alphabetically, in
    both the introspection result and the exported SDL, so related fields such
    as userById and userByName appear next to each other. It is off by default.
    🍓
---

Add a new `sort_schema` option to `StrawberryConfig`. When enabled,
the schema's types, fields and arguments are sorted alphabetically, affecting both
the introspection result and the exported SDL. This makes it easier to find
related fields (for example `userById`, `userByName`) in the GraphiQL UI and in
exported `schema.graphql` files.

```python
import strawberry
from strawberry.schema.config import StrawberryConfig

schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(sort_schema=True),
)
```

It defaults to `False`, preserving the existing definition order.
