Release type: minor

This change allows documenting permissions in the GraphQL schema, either using directives or field descriptions:

```python+graphql
schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(permissions_directive=True)
)
---
directive @requiresPermissions(permissions: [String!]!) on FIELD_DEFINITION
type Query {
  user: String! @requiresPermissions(permissions: ["IsAuthenticated"])
}
```

or

```python+graphql
schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(permissions_description=True)
)
---
type Query {
  """
  Required permissions:
   - *IsAuthenticated*: User is not authenticated
  """
  user: String!
}
```
