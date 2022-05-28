---
title: Tools
---

# Tools

Strawberry provides some utility functions to help you build your GraphQL
server. All tools can be imported from `strawberry.tools`

---

### `create_type`

Create a Strawberry type from a list of fields.

```python
def create_type(name: str, fields: List[StrawberryField]) -> Type:
    ...
```

Example:

```python+schema
import strawberry
from strawberry.tools import create_type

@strawberry.field
def hello(info) -> str:
    return "World"

def get_name(info) -> str:
    return info.context.user.name

my_name = strawberry.field(name="myName", resolver=get_name)

Query = create_type("Query", [hello, my_name])

schema = strawberry.Schema(query=Query)
---
type Query {
  hello: String!
  myName: String!
}
```

---

### `merge_types`

Merge multiple Strawberry types into one. Example:

```python+schema
import strawberry
from strawberry.tools import merge_types


@strawberry.type
class QueryA:
    @strawberry.field
    def perform_a(self) -> str:
        ...


@strawberry.type
class QueryB:
    @strawberry.field
    def perform_b(self) -> str:
        ...


ComboQuery = merge_types("ComboQuery", (QueryB, QueryA))
schema = strawberry.Schema(query=ComboQuery)
---
type ComboQuery {
  performB: String!
  performA: String!
}
```
