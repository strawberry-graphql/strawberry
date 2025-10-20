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
def create_type(
    name: str,
    fields: List[StrawberryField],
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    extend: bool = False,
) -> Type: ...
```

Example:

<CodeGrid>

```python
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
```

```graphql
type Query {
  hello: String!
  myName: String!
}
```

</CodeGrid>

---

### `merge_types`

Merge multiple Strawberry types into one. Example:

<CodeGrid>

```python
import strawberry
from strawberry.tools import merge_types


@strawberry.type
class QueryA:
    @strawberry.field
    def perform_a(self) -> str: ...


@strawberry.type
class QueryB:
    @strawberry.field
    def perform_b(self) -> str: ...


ComboQuery = merge_types("ComboQuery", (QueryB, QueryA))
```

```graphql
type ComboQuery {
  performB: String!
  performA: String!
}
```

### `PartialType`

`PartialType` metaclass is used to extend your type but makes its all field
optional. Consider you have different types for each operation on the same model
such as `UserCreate`, `UserUpdate` and `UserQuery`. `UserQuery` should have id
field but the other does not. All fields of `UserQuery` and `UserUpdate` might
be optional. In this case instead of defining the same field for each type one
can define in a single type and extend it.

```py
from strawberry.tools import PartialType


@strawberry.type
class UserCreate:
    firstname: str
    lastname: str


@strawberry.type
class UserUpdate(UserCreate, metaclass=PartialType):
    pass


@strawberry.type
class UserQuery(UserCreate, metaclass=PartialType):
    id: Optional[strawberry.ID]
```

</CodeGrid>
