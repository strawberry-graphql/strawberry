Release type: patch

This release fixes schema codegen to support custom directive definitions. Previously, schemas containing custom directives like `@authz` would fail with `NotImplementedError: Unknown definition None`. Now directive definitions are gracefully skipped since they don't require code generation.

```graphql
directive @authz(resource: String!, action: String!) on FIELD_DEFINITION

type Query {
    hello: String! @authz(resource: "greeting", action: "read")
}
```

This also fixes the error message for truly unknown definition types to show the actual type name instead of `None`.
