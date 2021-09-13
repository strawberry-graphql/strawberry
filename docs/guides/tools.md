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

### `WithQueryDepthLimiter`

Extension to add a query depth limter validation rule that limits the complexity of queries by
their depth to protect against malicious queries.

```python
class QueryDepthLimiter(
    max_depth: int,
    ignore: Optional[List[Union[str, re.Pattern, Callable[[str], bool]]]] = None,
    callback: Optional[Callable[Dict[str, int]]] = None
):
    ...
```

| Parameter name | Type                                                            | Default | Description                                                                                                                               |
| -------------- | --------------------------------------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| max_depth      | `int`                                                           | N/A     | The maximum allowed depth for any operation in a GraphQL document                                                                         |
| ignore         | `Optional[List[Union[str, re.Pattern, Callable[[str], bool]]]]` | `None`  | Stops recursive depth checking based on a field name. Either a string or regexp to match the name, or a function that reaturns a boolean. |
| callback       | `Optional[Callable[[Dict[str, int]], None]]`                    | `None`  | Called each time validation runs. Receives an Object which is a map of the depths for each operation                                      |

Example:

```python
import strawberry
from strawberry.extensions import QueryDepthLimiter

# assuming you already have a Query type
schema = strawberry.Schema(
  Query,
  extensions=[
    # Add the depth limiter extension
    QueryDepthLimiter(max_depth=3),
  ]
)

result = schema.execute_sync(
    """
    query MyQuery {
      user {
        pets {
          owner {
            pets {
              name
            }
          }
        }
      }
    }
    """
  )
)
assert len(result.errors) == 1
assert result.errors[0].message == "'MyQuery' exceeds maximum operation depth of 3"
```
