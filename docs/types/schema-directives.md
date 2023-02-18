---
title: Schema Directives
---

# Schema Directives

Strawberry supports
[schema directives](https://spec.graphql.org/June2018/#TypeSystemDirectiveLocation),
which are directives that don't change the behavior of your GraphQL schema but
instead provide a way to add additional metadata to it.

> For example our [Apollo Federation integration](../guides/federation.md) is
> based on schema directives.

Let's see how you can implement a schema directive in Strawberry, here we are
creating a directive called `keys` that can be applied to
[Object types definitions](./object-types.md) and accepts one parameter called
`fields`. Note that directive names, by default, are converted to camelCase on
the GraphQL schema.

Here's how we can use it in our schema:

```python
import strawberry
from strawberry.schema_directive import Location


@strawberry.schema_directive(locations=[Location.OBJECT])
class Keys:
    fields: str


from .directives import Keys


@strawberry.type(directives=[Keys(fields="id")])
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

## Overriding field names

You can use `strawberry.directive_field` to override the name of a field:

```python
@strawberry.schema_directive(locations=[Location.OBJECT])
class Keys:
    fields: str = strawberry.directive_field(name="as")
```

## Locations

Schema directives can be applied to many different parts of a schema. Here's the
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
