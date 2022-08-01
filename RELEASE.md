Relase type: patch

This release adds support for priting custom scalar used only on
schema directives, for example the following schema:

```python
SensitiveConfiguration = strawberry.scalar(str, name="SensitiveConfiguration")

@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Sensitive:
    config: SensitiveConfiguration

@strawberry.type
class Query:
    first_name: str = strawberry.field(directives=[Sensitive(config="Some config")])
```

prints the following:

```graphql
directive @sensitive(config: SensitiveConfiguration!) on FIELD_DEFINITION

type Query {
    firstName: String! @sensitive(config: "Some config")
}

scalar SensitiveConfiguration
```

while previously it would omit the definition of the scalar.
