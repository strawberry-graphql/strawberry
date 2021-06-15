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

Create a validator to limit the complexity of queries by their depth to protect against malicious
queries.

```python
from graphql import ValidationRule

class DepthLimitOptions(TypedDict):
    ignore: List[Union[str, re.Pattern, Callable[[str], bool]]]

def depth_limit_validator(
    max_depth: int,
    options: Optional[DepthLimitOptions] = None,
    callback: Optional[Callable[Dict[str, int]]] = None
) -> ValidationRule:
    ...
```

| Parameter name   | Type                       | Default | Description                                                                                            |
| ---------------- | -------------------------- | ------- | ------------------------------------------------------------------------------------------------------ |
| max_depth        | `int`                      | N/A     | The maximum allowed depth for any operation in a GraphQL document                                      |
| options   | `Optional[DepthLimitOptions]` | `None` |                                                                                                             |
| options.ignore   | `List[Union[str, re.Pattern, Callable[[str], bool]]]` | `None` | Stops recursive depth checking based on a field name. Either a string or regexp to match the name, or a function that reaturns a boolean. |
| callback         | `Optional[Callable[[Dict[str, int]], None]]` | `None` | Called each time validation runs.  Receives an Object which is a map of the depths for each operation |

Example:

```python
import strawberry
from strawberry.schema import default_validation_rules
from strawberry.tools import depth_limit_validator


# Add the depth limit validator to the list of default validation rules
validation_rules = (
  default_validation_rules + [depth_limit_validator(3)]
)

# assuming you already have a schema
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
    """,
    validation_rules=validation_rules,
  )
)
assert len(result.errors) == 1
assert result.errors[0].message == "'MyQuery' exceeds maximum operation depth of 3"
```
