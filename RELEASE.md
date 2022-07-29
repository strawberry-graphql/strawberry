Release type: minor

This PR adds support for adding schema directives to the schema of
your GraphQL API. For printing the following schema:

```python
@strawberry.schema_directive(locations=[Location.SCHEMA])
class Tag:
    name: str

@strawberry.type
class Query:
    first_name: str = strawberry.field(directives=[Tag(name="team-1")])

schema = strawberry.Schema(query=Query, schema_directives=[Tag(name="team-1")])
```

will print the following:

```graphql
directive @tag(name: String!) on SCHEMA

schema @tag(name: "team-1") {
    query: Query
}

type Query {
    firstName: String!
}
"""
```
