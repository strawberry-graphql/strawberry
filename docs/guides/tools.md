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

### `depth_limit_validator`

Limit the complexity of queries by their depth.

```python
class DepthLimitOptions(TypedDict):
    ignore: Union[str, re.Pattern, Callable[[str], bool]]

def depth_limit_validator(
  max_depth: int,  # The maximum allowed depth for any operation in a GraphQL document
  options: DepthLimitOptions = None,
  callback: Callable[Dict[str, int]] = None  # Called each time validation runs.  Receives an Object which is a map of the depths for each operation
) -> ValidationRule:
    ...
```

Example:

```python
import strawberry
from strawberry.schema import default_validation_rules
from strawberry.tools import depth_limit_validator


# assuming you already have a schema
result = schema.execute_sync(
  """
    query {
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
  """,
  validation_rules=(
    default_validation_rules
    + [depth_limit_validator(2)]
    )
)
assert result.errors
```
