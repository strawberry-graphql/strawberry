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
`UUID`, and `strawberry.scalars.JSON`). Other scalar names generate an
`Annotated` alias with a `strawberry.scalar(name=...)` definition. No scalar map
is required:

```python
from typing import Annotated

import strawberry

Email = Annotated[object, strawberry.scalar(name="Email")]


@strawberry.type
class Query:
    email: Email


schema = strawberry.Schema(query=Query)
```

SDL does not describe Python value types or conversion functions, so codegen
uses `object` and identity conversion as placeholders. Replace them with your
scalar's Python type, `serialize`, and `parse_value` as needed. Descriptions and
`@specifiedBy` URLs are preserved, including for SDL fragments without a schema
root: importing and using the generated alias carries its definition with it.
Unknown names such as `JSONObject` keep their GraphQL name rather than silently
being renamed to `JSON`. You can still use `Schema(scalar_map=...)` to override
an imported alias for a particular schema.
