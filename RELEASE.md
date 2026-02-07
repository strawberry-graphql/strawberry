Release type: minor

Remove all previously deprecated APIs and patterns.

### Upgrade commands

Some of the removed deprecations can be automatically fixed using the `strawberry upgrade` command:

- `strawberry upgrade annotated-union <path>` — converts `strawberry.union(..., types=(...))` to `Annotated[A | B, strawberry.union("Name")]`
- `strawberry upgrade update-imports <path>` — updates deprecated import paths to new locations
- `strawberry upgrade replace-scalar-wrappers <path>` — replaces deprecated scalar wrapper imports with standard library types

### All Removed Deprecations

| Deprecation | Deprecated In | Replacement |
|-------------|---------------|-------------|
| `info.field_nodes` property | 0.73.1 | `selected_fields` |
| Pydantic `fields` parameter | 0.82.0 | `strawberry.auto` annotations |
| `is_unset()` function | 0.109.0 | `value is UNSET` |
| `UNSET` import from `strawberry.arguments` | 0.109.0 | `from strawberry import UNSET` |
| `LazyType["Name", "module"]` syntax | 0.129.0 | `Annotated["Name", strawberry.lazy("module")]` |
| Sanic context dot notation | 0.146.0 | Dict-style access `context["request"]` |
| Sanic `json_encoder` parameter | 0.147.0 | Override `encode_json()` method |
| Sanic `json_dumps_params` parameter | 0.147.0 | Override `encode_json()` method |
| Extension legacy hooks (`on_request_start`, etc.) | 0.159.0 | Generator-based hooks (`on_operation`, etc.) |
| `Extension` import alias | 0.160.0 | `SchemaExtension` |
| Type definition aliases (`_type_definition`) | 0.187.0 | `__strawberry_definition__` |
| `types` parameter in `strawberry.union()` | 0.191.0 | `Annotated[A \| B, strawberry.union("Name")]` |
| `channel_listen` method | 0.193.0 | `listen_to_channel` context manager |
| `graphiql` parameter | 0.213.0 | `graphql_ide="graphiql"` |
| `asserts_errors` parameter | 0.246.0 | `assert_no_errors` |
| `ExecutionContext.errors` property | 0.276.2 | `pre_execution_errors` |
| `strawberry server` CLI command | 0.283.0 | `strawberry dev` |
| `debug-server` extra | 0.283.0 | `cli` extra |
| Scalar class wrapper pattern | 0.288.0 | `scalar_map` in `StrawberryConfig` |
