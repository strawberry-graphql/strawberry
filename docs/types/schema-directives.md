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

## Locations

Schema directives can be applied to many different parts of a schema, here's the
list of all the allowed locations:

| Name                   |                         | Description                                              |
| ---------------------- | ----------------------- | -------------------------------------------------------- |
| SCHEMA                 | `strawberry.Schema`     | The definition of a schema                               |
| SCALAR                 | `strawberry.scalar`     | The definition of a scalar                               |
| OBJECT                 | `strawberry.type`       | The definition of an object type                         |
| FIELD_DEFINITION       | `strawberry.field`      | The definition of a field on an object type or interface |
| ARGUMENT_DEFINITION    | `strawberry.argument`   | The definition of an argument                            |
| INTERFACE              | `strawberry.interface`  | The definition of an interface                           |
| UNION                  | `strawberry.union`      | The definition of an union                               |
| ENUM                   | `strawberry.enum`       | The definition of a enum                                 |
| ENUM_VALUE             | `strawberry.enum_value` | The definition of a enum value                           |
| INPUT_OBJECT           | `strawberry.input`      | The definition of an input object type                   |
| INPUT_FIELD_DEFINITION | `strawberry.field`      | The definition of a field on an input type               |

# TODO: explain why these can be useful!
