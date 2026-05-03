Release type: minor

`strawberry schema-codegen` now produces output that type-checks cleanly under
Pyright's default ruleset for user-defined custom scalars, and adds a
`-c / --config` option for telling codegen how specific scalars should be
emitted.

## Pyright-clean custom scalar output

Previously, an SDL like:

```graphql
scalar Foo

type Query {
  c: Foo!
}
```

generated a `Foo = strawberry.scalar(NewType("Foo", object), ...)` binding,
which fails three Pyright checks per scalar and uses the deprecated
`ScalarWrapper` pattern.

The generated output now uses a module-level `NewType` binding plus a
`scalar_map` registered through `StrawberryConfig` (the recommended Strawberry
API):

```python
from __future__ import annotations
import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.types.scalar import ScalarDefinition
from typing import NewType

Foo = NewType("Foo", object)


@strawberry.type
class Query:
    c: Foo


scalar_map: dict[object, ScalarDefinition] = {
    Foo: strawberry.scalar(name="Foo", serialize=lambda v: v, parse_value=lambda v: v),
}

schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(scalar_map=scalar_map),
)
```

The `scalar_map` is emitted as a module-level constant so it is preserved even
when codegen runs against a scalars-only SDL fragment, and so descriptions and
`@specifiedBy` URLs are never silently dropped.

## Config file

`strawberry schema-codegen` now accepts `-c / --config <file>` pointing at a
YAML config. The first available section is `scalars:`, a mapping from a
GraphQL scalar name to a `<module>:<object>` Python target. For each entry,
codegen imports the target instead of generating a `NewType` plus `scalar_map`
entry.

```yaml
# codegen.yaml
scalars:
  JSONObject: strawberry.scalars:JSON
  MyDecimal: my_app.scalars:MyDecimal
  Date: my_app.scalars:UnixDate
```

```shell
strawberry schema-codegen schema.graphql -c codegen.yaml
```

For a scalar named `JSONObject` mapped to `strawberry.scalars:JSON` the
generated code now contains `from strawberry.scalars import JSON as JSONObject`
and skips the `NewType` / `scalar_map` machinery entirely. Overrides win over
the built-in scalar mappings, so the same mechanism can redirect `Date`,
`JSON`, `UUID`, etc. to custom implementations.

Note: previous pre-release builds of this branch auto-mapped `JSONObject` to
`strawberry.scalars.JSON` as a hard-coded convention. That convention has been
removed — pass it through the config file instead.
