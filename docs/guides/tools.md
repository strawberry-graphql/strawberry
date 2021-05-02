---
title: Tools
---

# Tools

Strawberry provides some utility functions to help you build your GraphQL
server. All tools can be imported from `strawberry.tools`

---

### `create_type`

Create a Strawberry type from a list of StrawberryFields.

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
