Release type: minor

Two improvements to `strawberry schema-codegen`:

**Pyright-clean output for custom scalars.** Previously, `scalar Foo` generated
`Foo = strawberry.scalar(NewType("Foo", object), ...)` — the deprecated
`ScalarWrapper` pattern, which fails three Pyright checks per scalar. Output
now uses a module-level `NewType` binding plus a `scalar_map` registered
through `StrawberryConfig` (the recommended API), preserving descriptions and
`@specifiedBy` URLs:

```python
Foo = NewType("Foo", object)

scalar_map: dict[object, ScalarDefinition] = {
    Foo: strawberry.scalar(name="Foo", serialize=lambda v: v, parse_value=lambda v: v),
}

schema = strawberry.Schema(query=Query, config=StrawberryConfig(scalar_map=scalar_map))
```

**New `-c / --config <file>` flag.** Point codegen at a YAML config to control
how specific scalars are emitted. Today the only section is `scalars:`, a
mapping from a GraphQL scalar name to a `<module>:<object>` Python target —
codegen imports the target instead of generating a `NewType` for it.

```yaml
# codegen.yaml
scalars:
  JSONObject: strawberry.scalars:JSON
  MyDecimal: my_app.scalars:MyDecimal
```

```shell
strawberry schema-codegen schema.graphql -c codegen.yaml
```

Overrides win over the built-in scalar mappings, so `Date`, `JSON`, `UUID`,
etc. can also be redirected to custom implementations.
