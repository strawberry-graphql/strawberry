Release type: patch

This release adds support for priting custom enums used only on
schema directives, for example the following schema:

```python
@strawberry.enum
class Reason(str, Enum):
    EXAMPLE = "example"

@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Sensitive:
    reason: Reason

@strawberry.type
class Query:
    first_name: str = strawberry.field(
        directives=[Sensitive(reason=Reason.EXAMPLE)]
    )
```

prints the following:

```graphql
directive @sensitive(reason: Reason!) on FIELD_DEFINITION

type Query {
    firstName: String! @sensitive(reason: EXAMPLE)
}

enum Reason {
    EXAMPLE
}
```

while previously it would omit the definition of the enum.
