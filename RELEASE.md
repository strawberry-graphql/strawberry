Release type: patch

`strawberry schema-codegen` now produces output that type-checks cleanly
under Pyright's default ruleset for user-defined custom scalars, and the
`JSON` / `JSONObject` registry entries have been repaired.

Previously, an SDL like:

```graphql
scalar JSON
scalar JSONObject
scalar Foo

type Query {
  a: JSON!
  b: JSONObject!
  c: Foo!
}
```

generated code that referenced the non-existent `strawberry.JSON`
attribute (raising `AttributeError` at schema construction) and emitted
the deprecated `ScalarWrapper` pattern for `Foo` (`Foo = strawberry.scalar(NewType("Foo", object), ...)`),
which fails three Pyright checks per scalar.

The generated output now uses `from strawberry.scalars import JSON`,
`from strawberry.scalars import JSON as JSONObject` for the
community-standard `JSONObject` convention, and a module-level `NewType`
binding registered through `StrawberryConfig.scalar_map` (the recommended
Strawberry API for custom scalars) for arbitrary user-defined scalars:

```python
from __future__ import annotations
import strawberry
from strawberry.scalars import JSON
from strawberry.scalars import JSON as JSONObject
from strawberry.schema.config import StrawberryConfig
from strawberry.types.scalar import ScalarDefinition
from typing import NewType

Foo = NewType("Foo", object)


@strawberry.type
class Query:
    a: JSON
    b: JSONObject
    c: Foo


scalar_map: dict[object, ScalarDefinition] = {
    Foo: strawberry.scalar(name="Foo", serialize=lambda v: v, parse_value=lambda v: v),
}

schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(scalar_map=scalar_map),
)
```

The `scalar_map` is emitted as a module-level constant so it is preserved
even when codegen runs against a scalars-only SDL fragment (no
`Query`/`Mutation`/`Subscription`), and so descriptions and
`@specifiedBy` URLs are never silently dropped.
