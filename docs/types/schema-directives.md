---
title: Schema Directives
---

# Schema Directives

Strawberry supports
[schema directives](https://spec.graphql.org/June2018/#TypeSystemDirectiveLocation),
these directives don't change the behavior of your GraphQL schema but they
provided a way to add additional metadata to your schema.

> For example our [Apollo Federation integration](../guides/federation.md) is
> based on schema directives.

Here's how you can implement a schema directive in Strawberry:

```python
import strawberry

# TODO: where should location come from?

@strawberry.schema_directive(locations=[OBJECT])
class Keys:
  fields: str
```

Here we are creating a directive called `keys` (the name will, by default
converted to camelCase) that can be applied to
[Object types definitions](./object-types.md) and that accepts one parameter
called `fields`.

Here's how we can use it in our schema:

```python
import strawberry

@strawberry.type(directives=Keys(fields="id"))
class User:
    id: strawberry.ID
    name: str
```

This will result in the following schema:

```graphql
type User @keys(fields: "id") {
  id: ID!
  name: String!
}
```

# TODO: explain why these can be useful!
