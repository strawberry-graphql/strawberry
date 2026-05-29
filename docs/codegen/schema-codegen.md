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

## Writing the result to a file

By default the generated code is printed to stdout. Pass `-o / --output` to
write it to a file instead — parent directories are created as needed:

```shell
strawberry schema-codegen schema.graphql --output schema.py
```

## Custom scalars

Built-in scalars (`Int`, `Float`, `String`, `Boolean`, `ID`, `JSON`, `UUID`,
`Decimal`, `Date`, `Time`, `DateTime`) are mapped to their Python / Strawberry
equivalents automatically. Any other `scalar` declaration is emitted as a
`NewType` registered through `StrawberryConfig.scalar_map`, with a placeholder
identity `serialize` / `parse_value`:

```graphql
scalar Foo

type Query {
  data: Foo!
}
```

```python
from __future__ import annotations
import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.types.scalar import ScalarDefinition
from typing import NewType

Foo = NewType("Foo", object)


@strawberry.type
class Query:
    data: Foo


scalar_map: dict[object, ScalarDefinition] = {
    Foo: strawberry.scalar(name="Foo", serialize=lambda v: v, parse_value=lambda v: v),
}

schema = strawberry.Schema(query=Query, config=StrawberryConfig(scalar_map=scalar_map))
```

You will typically want to replace those identity functions with real
serialization logic before using the generated schema in production.

## Config file

Pass `-c / --config <file>` to point codegen at a YAML config that controls how
specific scalars are emitted. Today the only section is `scalars:`, a mapping
from a GraphQL scalar name to a `<module>:<object>` Python target:

```yaml
# codegen.yaml
scalars:
  JSONObject: strawberry.scalars:JSON
  MyDecimal: my_app.scalars:MyDecimal
  Date: my_app.scalars:UnixDate
```

For each entry, codegen imports the target instead of generating a `NewType`
plus `scalar_map` entry:

- when `<object>` matches the GraphQL scalar name →
  `from <module> import <object>`
- when they differ → `from <module> import <object> as <ScalarName>`

Given the SDL:

```graphql
scalar JSONObject

type Query {
  data: JSONObject!
}
```

and the config above:

```shell
strawberry schema-codegen schema.graphql -c codegen.yaml
```

produces:

```python
import strawberry
from strawberry.scalars import JSON as JSONObject


@strawberry.type
class Query:
    data: JSONObject


schema = strawberry.Schema(query=Query)
```

`JSONObject` is the canonical example: Strawberry does not ship a `JSONObject`
scalar, but several schemas in the wild use that name as a synonym for `JSON`.
Pointing it at `strawberry.scalars:JSON` via the config is the recommended way
to wire that convention up — it is intentionally not a built-in default.

Overrides win over the built-in scalar mappings, so you can also redirect
`Date`, `JSON`, `UUID`, etc. to custom implementations. Any scalar mentioned in
the config is excluded from the generated `scalar_map` regardless of whether it
is normally a built-in or unknown scalar.
