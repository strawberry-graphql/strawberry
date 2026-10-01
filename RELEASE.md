Release type: minor

This release improves schema codegen to generate Python stub classes for custom directive definitions. Previously, schemas containing custom directives would fail with `NotImplementedError`. Now directive definitions are converted to Strawberry schema directive classes.

For example, this GraphQL schema:
```graphql
directive @authz(resource: String!, action: String!) on FIELD_DEFINITION

type Query {
    hello: String! @authz(resource: "greeting", action: "read")
}
```

Now generates:
```python
from strawberry.schema_directive import Location


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Authz:
    resource: str
    action: str
```

Note: The generated directives are stubs - they don't contain any behavior logic, which must be implemented separately.

This also fixes the error message for unknown definition types to show the actual type name instead of `None`.
