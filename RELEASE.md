Release type: minor

This release adds support for lexicographic (alphabetical) sorting of GraphQL
schema fields through a new configuration option.

Added a `sort_schema` configuration option to `StrawberryConfig` that allows
users to enable alphabetical sorting of schema types and fields. When enabled,
the schema uses GraphQL's built-in `lexicographic_sort_schema` function to sort
all types, fields, and other schema elements alphabetically, making the
introspection UI easier to navigate.

**Usage Example:**

```python
import strawberry
from strawberry.schema.config import StrawberryConfig


@strawberry.type
class Query:
    user_by_name: str
    user_by_id: str
    user_by_email: str


# Enable schema sorting
schema = strawberry.Schema(query=Query, config=StrawberryConfig(sort_schema=True))

# The printed schema will now have fields sorted alphabetically:
# type Query {
#   userByEmail: String!
#   userById: String!
#   userByName: String!
# }
```

**Features:**

- Sorts all schema elements alphabetically (types, fields, enums, etc.)
- Disabled by default to maintain backward compatibility
- Works with all schema features (mutations, subscriptions, interfaces, unions,
  etc.)
- Compatible with other config options like `auto_camel_case`

This makes GraphQL introspection UIs (typically at `/graphql`) much easier to
navigate by grouping related fields together alphabetically rather than in
definition order.
