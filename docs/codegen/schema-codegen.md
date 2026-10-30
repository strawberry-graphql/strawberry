---
title: Schema codegen
---

# Schema codegen

Strawberry supports code generation from SDL files.

Let's assume we have the following SDL file:

```graphql
type Query {
  user: User
}

type User {
  id: ID!
  name: String!
}
```

by running the following command:

```shell
strawberry schema-codegen schema.graphql
```

we'll get the following output:

```python
import strawberry


@strawberry.type
class Query:
    user: User | None


@strawberry.type
class User:
    id: strawberry.ID
    name: str


schema = strawberry.Schema(query=Query)
```

## Custom scalars

Known scalars such as `Date`, `UUID`, and `JSON` use their Python types (`date`,
`UUID`, and `strawberry.scalars.JSON`). Other scalar names generate a `NewType`
and a module-level `scalar_map` containing `strawberry.scalar(name=...)`
definitions. Generated schemas register these definitions through
`StrawberryConfig.scalar_map`:

```python
from typing import NewType

import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.types.scalar import ScalarDefinition

Email = NewType("Email", object)


@strawberry.type
class Query:
    email: Email


scalar_map: dict[object, ScalarDefinition] = {
    Email: strawberry.scalar(
        name="Email", serialize=lambda value: value, parse_value=lambda value: value
    )
}

schema = strawberry.Schema(query=Query, config=StrawberryConfig(scalar_map=scalar_map))
```

Replace the identity serialization and parsing functions with your scalar's
implementation as needed. Descriptions and `@specifiedBy` URLs are preserved in
the scalar definitions. For SDL fragments without a schema root, codegen still
emits `scalar_map`; pass it to your schema configuration when combining
fragments. Unknown names such as `JSONObject` keep their GraphQL name rather
than silently being renamed to `JSON`.
